from rest_framework.test import APITestCase
from inspections.serializers import InspectionEditSerializer, RemarkSerializer
from inspections.models import InspectionAnswer
from work_orders.models import WorkOrderForm
from rest_framework.test import APIClient, APIRequestFactory
from users.factories import AerosimpleUserFactory, RoleFactory,\
    GroupFactory
from users.models import PermissionConfig
from urllib.parse import urlencode


class FormTestCase(APITestCase):
    def setUp(self):
        self.schema = {
            "id": "inspection",
            "version": 1,
            "fields": [
              {
                "id": "d1",
                "type": "string",
                "title": "Date of Inspection",
                "required": True
              },
              {
                "id": "d2",
                "type": "string",
                "title": "Inspected by",
                "required": True
              },
              {
                "id": "d3",
                "type": "string",
                "title": "Weather Conditions",
                "required": True
              },
              {
                "id": "d4",
                "type": "string",
                "title": "Type of Inspection",
                "required": True
              },
              {
                "id": "d5",
                "type": "string",
                "title": "Shift",
                "required": True
              },
              {
                "id": "1",
                "type": "inspection",
                "title": "Inspection Field 1",
                "status_options": {
                  "pass": "Pass",
                  "fail": "Fail"
                },
                "checklist": [
                  {
                    "key": "CH1",
                    "value": "Option one?"
                  },
                  {
                    "key": "CH2",
                    "value": "option two?"
                  }
                ],
                "required": True
              },
              {
                "id": "2",
                "type": "inspection",
                "title": "Inspection Field 2",
                "status_options": {
                  "pass": "Satisfactory",
                  "fail": "Unsatisfactory"
                },
                "checklist": [
                  {
                    "key": "CH1",
                    "value": "checklist item 1"
                  },
                  {
                    "key": "CH2",
                    "value": "checklist item 2"
                  }
                ],
                "required": True
              }
            ],
            "sections": [
              {
                "id": "SEC1",
                "title": "Details",
                "fields": [
                  "d1",
                  "d2",
                  "d3",
                  "d4",
                  "d5"
                ]
              },
              {
                "id": "SEC2",
                "title": "Checklist",
                "fields": [
                  "1",
                  "2"
                ]
              }
            ],
            "pages": [
              {
                "id": "PAGE1",
                "title": "Inspection",
                "sections": [
                  "SEC1"
                ]
              },
              {
                "id": "PAGE2",
                "title": "Inspection",
                "sections": [
                  "SEC2"
                ]
              }
            ]
        }

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

        ans = {
          "title": "Hello",
          "icon": "icon-2",
          "schema": self.schema,
          "additionalInfo": '',
          "status": 1
        }

        factory = APIRequestFactory()
        request = factory.post('/api/inspections/', ans, format='json')
        request.user = self.aerouser.user

        serializer = InspectionEditSerializer(
            data=ans,
            context={'request': request}
        )

        self.assertEqual(serializer.is_valid(), True)
        serializer.save()
        self.inspection = serializer.instance

        inspection_answer = {
            "inspected_by": self.aerouser,
            "created_by": self.aerouser,
            "inspection_date": "2019-01-11T19:36:55.975Z",
            "inspection": self.inspection.versions.first(),
            "issues": 1,
            "response": {
                "d1": "2019-01-11T19:36:55.975Z",
                "d2": "John Doe",
                "d3": "Sunny",
                "d4": "Safety self inspection",
                "d5": "Day shift",
                "1": {
                    "CH1": False,
                    "CH2": True
                },
                "2": {
                    "CH1": True,
                    "CH2": True
                }
            }
        }

        self.answer = InspectionAnswer(**inspection_answer)
        self.answer.save()

    def test_inspection_create(self):
        """Test the creation of inspection."""

        ans = {
          "title": "Hello",
          "icon": "icon-2",
          "schema": self.schema
        }

        serializer = InspectionEditSerializer(data=ans)
        self.assertEqual(serializer.is_valid(), True)

    def test_inspection_with_one_page(self):
        """Test the validations of inspection with only one page."""

        newschema = self.schema

        newschema['pages'][0]['sections'].append('SEC2')
        del newschema['pages'][1]

        ans = {
          "title": "Hello",
          "icon": "icon-2",
          "schema": newschema
        }

        serializer = InspectionEditSerializer(data=ans)

        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(
          serializer.errors['schema'],
          ["An Inspection schema must have exactly two pages"]
        )

    def test_inspection_with_other_fieldtype(self):
        """Test the validations of inspection with only one page."""

        newschema = self.schema.copy()

        newschema['fields'][6]['type'] = 'string'
        del newschema['fields'][6]['status_options']
        del newschema['fields'][6]['checklist']

        ans = {
          "title": "Hello",
          "icon": "icon-2",
          "schema": newschema
        }

        serializer = InspectionEditSerializer(data=ans)

        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(
          serializer.errors['schema'],
          ["All fields in second page must be of type inspection"]
        )

    def test_remark(self):
        ans = {
            "title": "Hello",
            "icon": "icon-2",
            "schema": self.schema,
            "additionalInfo": '',
            "status": 1
        }

        factory = APIRequestFactory()
        request = factory.post('/api/inspections/', ans, format='json')
        request.user = self.aerouser.user

        serializer = InspectionEditSerializer(
            data=ans,
            context={'request': request}
        )

        self.assertEqual(serializer.is_valid(), True)
        serializer.save()
        remark_data = {
            "answer": self.answer.id,
            "field_reference": '1',
            "item_reference": 'CH1',
            "text": "This is a remark"
        }

        remark_serializer = RemarkSerializer(data=remark_data)
        self.assertEqual(remark_serializer.is_valid(), True)

    def test_remark_incorrect_field(self):

        remark_data = {
            "answer": self.answer.id,
            "field_reference": 'not_a_field',
            "item_reference": 'CH1',
            "text": "This is a remark"
        }

        remark_serializer = RemarkSerializer(data=remark_data)
        self.assertEqual(remark_serializer.is_valid(), False)
        self.assertEqual(
            remark_serializer.errors['field_reference'],
            ["'not_a_field' is not a valid field id in the version schema"]
        )

    def test_remark_incorrect_item(self):

        remark_data = {
            "answer": self.answer.id,
            "field_reference": '1',
            "item_reference": 'NOT_AN_ITEM',
            "text": "This is a remark"
        }

        remark_serializer = RemarkSerializer(data=remark_data)
        self.assertEqual(remark_serializer.is_valid(), False)
        self.assertEqual(
            remark_serializer.errors['item_reference'],
            ["'NOT_AN_ITEM' is not a valid checklist item for that inspection"]
        )

    def test_remark_incorrect_field_type(self):

        remark_data = {
            "answer": self.answer.id,
            "field_reference": 'd1',
            "item_reference": 'CH1',
            "text": "This is a remark"
        }

        remark_serializer = RemarkSerializer(data=remark_data)
        self.assertEqual(remark_serializer.is_valid(), False)
        self.assertEqual(
            remark_serializer.errors['field_reference'],
            ["field 'd1' must be of type inspection"]
        )

    def test_positive_answer_with_workorder_associated(self):
        workorder_form = WorkOrderForm()
        workorder_form.airport = self.aerouser.airport
        workorder_form.save()

        self.aerouser.airport.safety_self_inspection = self.inspection
        self.aerouser.airport.save()

        # self.assertEqual(workorder_form.id, True)

        data = {
            "report_date": "2019-01-14T13:41:00-03:00",
            "logged_by": self.aerouser.id,
            "location": '{"type":"Point","coordinates":[2.0829279161989693, 41.29141527748391]}',
            "category": "Inspection Field 1",
            "priority": 1,
            "subcategory": "checklist item 2",
            "problem_description": "Description",
            "response": '{}',
            "category_id": "1",
            "subcategory_id": "CH2"
        }

        self.apiClient.post(
            '/api/work_orders/', urlencode(data),
            content_type="application/x-www-form-urlencoded")

        response = self.apiClient.post(
            '/api/inspections/{}/create_empty_inspection/'.format(
                self.inspection.id), format='json')
        self.assertEqual(response.data['result'], 'Answer created')

        ans = {
            "answer_id": response.data['id'],
            "response": {
                "d1": "2019-01-11T19:36:55.975Z",
                "d2": "John Doe",
                "d3": "Sunny",
                "d4": "Safety self inspection",
                "d5": "Day shift",
                "1": {
                    "CH1": True,
                    "CH2": True
                },
                "2": {
                    "CH1": True,
                    "CH2": True
                }
            },
            "date": "2019-01-11T19:36:55.975Z",
            "weather": {"title": "sfd"},
            "type": "sdf",
            "inspected_by": self.aerouser.id,
            "created_by": self.aerouser.id
        }

        response2 = self.apiClient.post(
            '/api/inspections/{}/complete_inspection/'.format(
                self.inspection.id), ans, format='json')

        self.assertEqual(
            response2.data['inspection_answer'][0],
            ('The item with Category 1 and subcategory CH2 has a '
             'workorder associated, thus response must be false.'))

        ans["response"]["1"]["CH2"] = False

        response2 = self.apiClient.post(
            '/api/inspections/{}/complete_inspection/'.format(
                self.inspection.id), ans, format='json')

        self.assertEqual(response2.data['result'], 'Answer updated')
