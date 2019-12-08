import boto3 
import json
from django.core.serializers.json import DjangoJSONEncoder

import xml.etree.cElementTree as et

from django.conf import settings

def is_svg(f):
    tag = None
    try:
        for event, el in et.iterparse(f.open(mode='r'), ('start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'


class DynamoDbModuleUtility:
    """
        Get Module permission from Dynamo db and access.
    """

    @staticmethod
    def get_module_permissions(airport_code):
        if settings.AIRPORT_PLAN_ENABLE:
            if airport_code not in settings.AIRPORT_PLANS:
                DynamoDbModuleUtility.fetch_module_permissions(airport_code)


    @staticmethod
    def fetch_module_permissions(airport_code):
        """
            Used to return all module permissions to save in session
        """
        if settings.AIRPORT_PLAN_ENABLE:
            dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_DEFAULT_REGION)
            airport_table = dynamodb.Table(settings.APP_PREFIX + 'airport')
            airport_key = '{0}_{1}'.format(airport_code, settings.BACKEND_ID)
            airport_object = airport_table.get_item(Key={"id": airport_key})
            if 'Item' in airport_object.keys() and 'plan' in airport_object['Item']:
                settings.AIRPORT_PLANS[airport_code] = json.loads(json.dumps(
                    airport_object['Item']['plan'], cls=DjangoJSONEncoder))
            else:
                settings.AIRPORT_PLANS[airport_code] = {}

    @staticmethod
    def return_module_attribute(airport_code, module_key, attribute):
        """
            Check if the module key exists in dynamodb data
        """
        DynamoDbModuleUtility.get_module_permissions(airport_code)
        if settings.AIRPORT_PLAN_ENABLE and airport_code in settings.AIRPORT_PLANS:
            plan = settings.AIRPORT_PLANS[airport_code]
            for module in plan['modules']:
                if module['key'] == module_key:
                    if 'attributes' in module.keys() and attribute in module['attributes'].keys():
                        return module['attributes'][attribute]
        return None
    
    @staticmethod
    def get_plan_data(airport_code):
        """
            Return module based on module permissions
        """
        DynamoDbModuleUtility.get_module_permissions(airport_code)
        if settings.AIRPORT_PLAN_ENABLE:
            if airport_code in settings.AIRPORT_PLANS:
                return settings.AIRPORT_PLANS[airport_code]
            return {}
        else:
            return {}
    
    @staticmethod
    def has_module_permissions(airport_code, module_key):
        """
            Return module based on module permissions
        """
        DynamoDbModuleUtility.get_module_permissions(airport_code)
        if settings.AIRPORT_PLAN_ENABLE:
            if airport_code in settings.AIRPORT_PLANS:
                plan = settings.AIRPORT_PLANS[airport_code]
                for module in plan['modules']:
                    if module['key'] == module_key and module.get('enabled', 'false') == 'true':
                        return True
                return False
            return False
        else:
            return True
    
    @staticmethod
    def has_sources_permissions(airport_code, source_key):
        """
            Return source based on sources permissions
        """
        DynamoDbModuleUtility.get_module_permissions(airport_code)
        if settings.AIRPORT_PLAN_ENABLE:
            if airport_code in settings.AIRPORT_PLANS:
                plan = settings.AIRPORT_PLANS[airport_code]
                for source in plan['sources']:
                    if source['key'] == source_key and source.get('enabled', 'false') == 'true':
                        return True
                return False
            return False
        else:
            return True
