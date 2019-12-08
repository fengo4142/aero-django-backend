from django.utils import timezone
from django.forms import model_to_dict
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from tasks.serializers import (TaskSerializer, OccurrenceSerializer,
                               RuleSerializer)

from tasks.models import Task, TaskOccurrence
from tasks.utils import create_task
from users.models import AerosimpleUser, Role
from schedule.models import Rule
from schedule.periods import Period
from forms.utils import DRAFT
from airport.permissions import AirportHasTaskPermission
from users.serializers import (AerosimpleUserDisplaySerializer , RoleSimpleSerializer, AerosimpleUserAssignmentSerializer)
from django.conf import settings
from django.template.loader import render_to_string
import boto3
import datetime
import logging
import json
from botocore.exceptions import ClientError

logger = logging.getLogger('backend')
def SendMailToTask(airportId,taskId):
    task= Task.objects.get(id=taskId)
    emails = ''
    logger.info(taskId)
    logger.info(airportId)
   
    images = {
        'background': settings.MEDIA_URL + 'notifications/background.png',
        'logo': settings.MEDIA_URL + 'notifications/logo.png',
        'plane': settings.MEDIA_URL + 'notifications/plane.png',
        'curve': settings.MEDIA_URL + 'notifications/curve.png',
        'welcome': settings.MEDIA_URL + 'notifications/welcome-email.png',
        'rectangle': settings.MEDIA_URL + 'notifications/Rectangle.png',
    }
    context={
        'images':images,
        'task':task,
    }
    if(task.assigned_user):
        task= Task.objects.get(id=taskId)
        emails= task.assigned_user.user.email
    else:
        task= Task.objects.get(id=taskId) 
        roles = AerosimpleUserAssignmentSerializer(
           AerosimpleUser.objects.filter(roles=task.assigned_role, airport_id = airportId, system_generated	= False),
           many=True
        ).data

        for l in range(len(roles)):
            emails = emails + roles[l]['email'] + ','

    logger.info(emails)  
   
    html_string = render_to_string('task assigned.html', context=context)
    
    if emails:
        RECIPIENT  = emails.rstrip(',').split(',')
        SUBJECT = 'Task'
        BODY_HTML = html_string
        CHARSET = "UTF-8"
        client = boto3.client('ses',region_name=settings.AWS_REGION)
        try:
            response = client.send_email(
                Destination={
                    'ToAddresses': RECIPIENT
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        }
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=settings.EMAIL_HOST_USER,
                ConfigurationSetName=settings.CONFIGURATION_SET,
            )
        except ClientError as e:
            logger.info(e.response['Error']['Message'])
        else:
            logger.info("Email sent! Message ID:"),
            logger.info(response['MessageId'])
        return True
    else:
        return True


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        if self.request.user:
            return Task.objects.exclude(inspection__versions__status=DRAFT)
        return Task.objects.none()

    @staticmethod
    def get_user_tasks(user):
        # getting tasks assigned to me
        my_tasks = Task.objects.filter(
                assigned_user = user.aerosimple_user)
        
        # getting tasks assigned to my role
        my_role_tasks = Task.objects.filter(
                assigned_role__in=user.aerosimple_user.roles.all())

        all_task = (my_tasks | my_role_tasks)
        return all_task.exclude(inspection__versions__status=DRAFT)

    def get_my_task(self):
        if self.request.user:
            return TaskViewSet.get_user_tasks(self.request.user)
        return Task.objects.none()

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated,AirportHasTaskPermission],
            'occurrences': [IsAuthenticated,AirportHasTaskPermission],
            'delegated': [IsAuthenticated,AirportHasTaskPermission],
            'completed': [IsAuthenticated,AirportHasTaskPermission],
            'retrieve': [IsAuthenticated,AirportHasTaskPermission],
            'delete': [IsAuthenticated, AirportHasTaskPermission],
            'update': [IsAuthenticated, AirportHasTaskPermission],
            'create': [IsAuthenticated, AirportHasTaskPermission],
            'partial_update': [IsAuthenticated, AirportHasTaskPermission],
            'toggle_complete_task': [IsAuthenticated, AirportHasTaskPermission],
            'update_occurrence': [IsAuthenticated, AirportHasTaskPermission]
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        # self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    @staticmethod
    def get_task_occurences(user):
        tasks = TaskViewSet.get_user_tasks(user)
        today = datetime.datetime.now()
        end_date = (today + datetime.timedelta(days=(7 - today.weekday() + 7)))

        this_period = Period(tasks.all(), today, end_date)
        result = this_period.get_occurrences()
        result.sort(key=lambda r: r.end)

        overdue = TaskViewSet.get_task_overdue(user)

        no_due_date = tasks.filter(end=datetime.datetime.fromtimestamp(0))
        this_period_2 = Period(
            no_due_date.all(),
            datetime.datetime.fromtimestamp(-1),
            datetime.datetime.fromtimestamp(1)
        )
        no_due_date_occurrences = this_period_2.get_occurrences()
        res = list(
            filter(lambda x: x.id is None or not x.task_occurrences.completed,
                   result + overdue + no_due_date_occurrences)
        )
        data = OccurrenceSerializer(res, many=True).data
        if data is not None:
            return list(filter(lambda x: ((x['event']['airport'] == None or x['event']['airport'] == user.aerosimple_user.airport_id) and
                        (x['event']['assigned_role'] == None or x['event']['assigned_role']['airport_id'] == user.aerosimple_user.airport_id)), data))
            # return data
        return []

    @action(detail=False, methods=['get'])
    def occurrences(self, request):
        return Response(
            TaskViewSet.get_task_occurences(self.request.user)
        )

    @staticmethod
    def get_task_overdue(user):
        """
        Get overdue tasks, ie. past ocurrences not persisted and not completed.
        When completing an ocurrence the Ocurrence instance is persisted, so
        ocurrence without pk are incompleted.
        """

        tasks = TaskViewSet.get_user_tasks(user)
        today = datetime.datetime.now()

        this_period = Period(
            tasks.all(), datetime.datetime.fromtimestamp(0), today)

        result = list(
            filter(lambda x: x.id is None or not x.task_occurrences.completed,
                   this_period.get_occurrences())
        )
        result.sort(key=lambda r: r.end)
        return result

    def get_overdue(self, request):
        TaskViewSet.get_task_overdue(self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_complete_task(self, request, pk=None):
        task = self.get_object()
        data = request.data
        date = datetime.datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%SZ')
        occurrence = task.get_occurrence(date)
        occurrence.save()
        task_occurrence, created = TaskOccurrence.objects.get_or_create(
            task=task,
            occurrence=occurrence
        )
        task_occurrence.completed = not task_occurrence.completed
        task_occurrence.save()   
        return Response(OccurrenceSerializer(occurrence).data)

    @action(detail=False, methods=['get'])
    def delegated(self, request):
        tasks = Task.objects.filter(
            creator=self.request.user).exclude(
                assigned_user=self.request.user.aerosimple_user).exclude(
                    assigned_role__in=self.request.user.aerosimple_user.roles.all())

        today = datetime.datetime.combine(
            datetime.datetime.now(),
            datetime.datetime.min.time()
        )
        end_date = (today + datetime.timedelta(days=(7 - today.weekday() + 7)))

        this_period = Period(tasks.all(), today, end_date)
        result = this_period.get_occurrences()
        result.sort(key=lambda r: r.end)
        data = OccurrenceSerializer(result, many=True).data
        if data is not None:
            return Response(list(filter(lambda x: ((x['event']['airport'] == None or x['event']['airport'] == self.request.user.aerosimple_user.airport_id) and
                        (x['event']['assigned_role'] == None or x['event']['assigned_role']['airport_id'] == self.request.user.aerosimple_user.airport_id)), data)))
            # return data
        return []

    @action(detail=False, methods=['get'])
    def completed(self, request):
        tasks = self.get_my_task().filter(
            task_occurrences__completed=True).distinct()
        result = []
        for t in tasks:
            result += t.occurrence_set.exclude(
                task_occurrences__completed=False)
        result.sort(key=lambda r: r.end)
        data = OccurrenceSerializer(result, many=True).data
        if data is not None:
            return Response(list(filter(lambda x: ((x['event']['airport'] == None or x['event']['airport'] == self.request.user.aerosimple_user.airport_id) and
                        (x['event']['assigned_role'] == None or x['event']['assigned_role']['airport_id'] == self.request.user.aerosimple_user.airport_id)), data)))
            # return data
        return []

    def create(self, request):
        data = request.data
        task = create_task(data, request.user)

        SendMailToTask(self.request.user.aerosimple_user.airport_id,task.id)
        return Response(TaskSerializer(task).data)

    def partial_update(self, request, pk=None, **kwargs):
        data = request.data
        instance = self.get_object()
        newrule = None
        if any(
            name in ['rule', 'assigned_user', 'assigned_role'] for name in data
        ):
            # If there is a new rule, we are ending the recurrence and creating
            # a new task with the new information.

            date = datetime.datetime.strptime(
                data['date'], '%Y-%m-%dT%H:%M:%SZ')
            instance.end_recurring_period = date
            instance.save()
            if 'rule' in data:
                ruleData = data.get('rule') if type(
                    data.get('rule')) is dict else json.loads(data.get('rule'))
                if 'id' in ruleData:
                    newrule = Rule.objects.get(pk=ruleData['id'])
                else:
                    rule, created = Rule.objects.get_or_create(
                        frequency=ruleData['frequency'],
                        params=ruleData['params']
                    )
                    if created:
                        rule.name = data.get('rule')[:20]
                    rule.save()
                    newrule = rule

            instance = Task.objects.get(pk=instance.pk)
            instance.pk = None
            instance.id = None
            instance.end_recurring_period = None
            if newrule is not None:
                instance.rule = newrule
            if instance.due_time is not None:
                hour = datetime.datetime.strptime(
                    data.get('due_time', None), "%H:%M%z").time()
            else:
                hour = datetime.datetime.max.time()
            final = datetime.datetime.combine(date, hour)
            instance.start = final
            instance.end = final
            instance.save()

        instance.description = data.get('additional_info', None)
        instance.title = data.get('name', None)

        if 'end_recurring_period' in data:
            erp = datetime.datetime.strptime(
                data.get('end_recurring_period', None), "%Y-%m-%d")
            instance.end_recurring_period = erp

        # Task specific fields
        if 'due_date' in data:
            dd = datetime.datetime.strptime(
                data.get('due_date', None), "%Y-%m-%d%z")
            instance.due_date = dd.date()
        if 'due_time' in data:
            hour = datetime.datetime.strptime(
                data.get('due_time', None), "%H:%M%z").time()
            for task_occurrence in instance.task_occurrences.all():
                occurrence = task_occurrence.occurrence
                final = datetime.datetime.combine(occurrence.start.date(), hour)
                occurrence.start = final
                occurrence.end = final
                occurrence.save()
        instance.due_time = data.get('due_time', None)
        instance.completed = data.get('completed', False)
        instance.attached = data.get('attached', None)
        instance.label = data.get('label', None)

        if 'assigned_user' in data:
            instance.assigned_user = AerosimpleUser.objects.get(
                id=int(data.get('assigned_user')))
            instance.assigned_role = None
        if 'assigned_role' in data:
            instance.assigned_role = Role.objects.get(
                id=int(data.get('assigned_role')))
            instance.assigned_user = None
        instance.save()

        return Response(TaskSerializer(instance).data)

    @action(detail=True, methods=['post'])
    def update_occurrence(self, request, pk=None):
        task = self.get_object()
        data = request.data

        if 'end_recurring_period' in data:
            erp = datetime.datetime.strptime(
                data.get('end_recurring_period', None), "%Y-%m-%d")
            task.end_recurring_period = erp
            task.save()

        date = datetime.datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%SZ')
        occurrence = task.get_occurrence(date)
        occurrence.description = data.get('additional_info', ' ')
        occurrence.title = data.get('name', None)
        if 'due_date' in data:
            date = datetime.datetime.strptime(
                data.get('due_date', None), "%Y-%m-%d%z")
            if 'due_time' in data:
                hour = datetime.datetime.strptime(
                    data.get('due_time', None), "%H:%M%z").time()
            else:
                hour = datetime.datetime.max.time()
            final = date.replace(
                hour=hour.hour, minute=hour.minute, second=hour.second
            )
            occurrence.start = final
            occurrence.end = final
        occurrence.save()
        task_occurrence, created = TaskOccurrence.objects.get_or_create(
            task=task,
            occurrence=occurrence
        )

        if task_occurrence is None:
            return Response(
                'Did not provide occurrence id or date',
                status=status.HTTP_400_BAD_REQUEST
            )
        task_occurrence.save()
        return Response(OccurrenceSerializer(occurrence).data)


class RuleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RuleSerializer
    queryset = Rule.objects.filter(
        name__in=["Daily", "Weekday", "Weekly", "Monthly", "Yearly"])
