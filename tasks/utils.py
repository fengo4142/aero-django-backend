import json
import datetime
import logging

from schedule.models import Calendar, Rule

from users.models import AerosimpleUser, Role
from tasks.models import Task
from django.template.defaultfilters import slugify

logger = logging.getLogger('backend.tasks')


def create_task(data, creator):
    task = Task()
    # If it the task has a due date we store it
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
        task.start = final
        task.end = final
    # if not has a due date, we set epoch 0, because dates fields
    # are required.
    else:
        task.start = datetime.datetime.fromtimestamp(0)
        task.end = datetime.datetime.fromtimestamp(0)

    task.end_recurring_period = data.get('end_recurring_period', None)
    task.description = data.get('additional_info', '')
    task.title = data.get('name', None)
    task.creator = creator
    if 'rule'in data:
        ruleData = data.get('rule') if type(
            data.get('rule')) is dict else json.loads(data.get('rule'))
        if 'id' in ruleData:
            task.rule = Rule.objects.get(pk=ruleData['id'])
        else:
            rule, created = Rule.objects.get_or_create(
                frequency=ruleData['frequency'],
                params=ruleData['params']
            )
            if created:
                rule.name = data.get('name')[:20]
            rule.save()
            task.rule = rule

    try:
        cal = Calendar.objects.get(
            name=creator.aerosimple_user.airport.code)
    except Calendar.DoesNotExist:
        cal = Calendar(name=creator.aerosimple_user.airport.code)
        cal.slug = slugify(cal.name)
        cal.save()
    task.calendar = cal

    # Task specific fields
    task.privacy = data.get('privacy', None)
    if 'due_date' in data:
        dd = datetime.datetime.strptime(
            data.get('due_date', None), "%Y-%m-%d%z")
        task.due_date = dd.date()
    task.due_time = data.get('due_time', None)
    task.completed = data.get('completed', False)
    task.attached = data.get('attached', None)
    task.label = data.get('label', None)

    if 'assigned_user' in data:
        task.assigned_user = AerosimpleUser.objects.get(
            id=int(data.get('assigned_user')))
    if 'assigned_role' in data:
        task.assigned_role = Role.objects.get(
            id=int(data.get('assigned_role')))
    task.airport = creator.aerosimple_user.airport
    task.save()

    return task
