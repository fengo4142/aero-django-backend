from rest_framework.test import APITestCase
from users.factories import AerosimpleUserFactory, GroupFactory, RoleFactory
from rest_framework.test import APIClient, APIRequestFactory
from users.models import PermissionConfig, AerosimpleUser
from django.contrib.auth.models import Permission


class FormTestCase(APITestCase):
    def setUp(self):

        # Login user
        self.aerouser = AerosimpleUserFactory()

        cfg = PermissionConfig.load()

        group = GroupFactory(permissions=cfg.permissions.all())
        role = RoleFactory(
            airport=self.aerouser.airport,
            permission_group=group)
        self.aerouser.roles.add(role)

        self.apiClient = APIClient()
        self.apiClient.force_authenticate(user=self.aerouser.user)

    def test_inspections_permissions(self):
        response = self.apiClient.get('/api/inspections/')
        self.assertEqual(response.status_code, 200)

        p = Permission.objects.get(codename="view_inspection")
        role = self.aerouser.roles.first()
        role.permission_group.permissions.remove(p)
        self.aerouser.roles.clear()
        self.aerouser.roles.add(role)

        user = AerosimpleUser.objects.get(pk=self.aerouser.pk)

        apiClient = APIClient()
        apiClient.force_authenticate(user=user.user)
        response = apiClient.get('/api/inspections/')
        self.assertEqual(response.status_code, 403)

    def test_inspections_create_permissions(self):
        data = {
          "title": "Hello", "icon": "icon-2",
          "schema": {
            "id": "inspection", "version": 1,
            "fields": [
                {"id": "d1", "type": "string", "title": "Date of Inspection", 
                 "required": False},
                {
                    "id": "1", "type": "inspection",
                    "title": "Inspection Field 1",
                    "status_options": {"pass": "Pass", "fail": "Fail"},
                    "checklist": [
                        {"key": "CH1", "value": "Option one?"},
                        {"key": "CH2", "value": "option two?"}
                    ],
                    "required": False
                }
            ],
            "sections": [
                {"id": "SEC1", "title": "Details", "fields": ["d1"]},
                {"id": "SEC2", "title": "Checklist", "fields": ["1"]}
            ],
            "pages": [
                {"id": "PAGE1", "title": "Inspection", "sections": ["SEC1"]},
                {"id": "PAGE2", "title": "Inspection", "sections": ["SEC2"]}
            ]
            },
          "additionalInfo": '',
          "status": 1
        }

        response = self.apiClient.post(
            '/api/edit_inspections/', data, format='json')
        self.assertEqual(response.status_code, 201)

        p = Permission.objects.get(codename="add_inspectionparent")
        role = self.aerouser.roles.first()
        role.permission_group.permissions.remove(p)
        self.aerouser.roles.clear()
        self.aerouser.roles.add(role)

        user = AerosimpleUser.objects.get(pk=self.aerouser.pk)

        self.apiClient.force_authenticate(user=user.user)
        response = self.apiClient.post('/api/inspections/', data, format='json')
        self.assertEqual(response.status_code, 403)
