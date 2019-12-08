from rest_framework import viewsets

# from forms.models import Form, Version, Answer
# from forms.serializers import FormSerializer, VersionSerializer, \
#     VersionCreateSerializer, VersionUpdateSerializer, AnswerSerializer, \
#     DetailAnswerSerializer


# class FormViewSet(viewsets.ModelViewSet):
#     queryset = Form.objects.all()
#     serializer_class = FormSerializer


# class VersionViewSet(viewsets.ModelViewSet):
#     queryset = Version.objects.all()
#     serializer_class = VersionSerializer

#     def get_serializer_class(self):
#         if self.action == 'list':
#             return VersionSerializer
#         elif self.action == 'update' or self.action == 'partial_update':
#             return VersionUpdateSerializer
#         return VersionCreateSerializer


# class AnswerViewSet(viewsets.ModelViewSet):
#     queryset = Answer.objects.all()

#     def get_serializer_class(self):
#         if self.action == 'retrieve':
#             return DetailAnswerSerializer
#         return AnswerSerializer
