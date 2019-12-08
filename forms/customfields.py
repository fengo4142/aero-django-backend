from pulpoforms.factories import FieldFactory
from pulpoforms.fields import Field
from pulpoforms.exceptions import FieldError
from django.contrib.gis.geos import GEOSGeometry, GEOSException
from django.contrib.gis.gdal import GDALException
from copy import copy

import json


class LocationField(Field):
    """
    Field type for strings.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty']
    )

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required', 'shape'
    ]

    ALLOWED_SHAPE_TYPES = [
        'Polygon', 'Point', 'LineString'
    ]

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'location',
        'title': '',
        'required': False,
        'shape': ''
    }

    @classmethod
    def validate_schema(cls, field):

        allowed_types = list(cls.ALLOWED_SHAPE_TYPES)
        if field['shape'] not in allowed_types:
            raise FieldError(
                "Type '{0}' is not a valid shape option."
                " Must be one of: "
                "'Polygon', 'Point' or 'LineString'".format(field['shape']))

        super().validate_schema(field)

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        if isinstance(value, dict):
            try:
                GEOSGeometry(json.dumps(value))
            except GEOSException:
                raise FieldError("geoJSON geometry is not valid")

            except (ValueError, TypeError, GDALException):
                raise FieldError("malformed geoJSON")

            if self.shape != value['type']:
                raise FieldError(
                    "geoJSON must be of type '{0}'".format(self.shape)
                )
        else:
            raise FieldError("value must be an object")

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('location', LocationField)


class InspectionField(Field):
    """
    Field type for strings.

    Handles validation of this field type schema and entries
    """

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required',
        'status_options', 'checklist'
    ]

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'inspection',
        'title': '',
        'required': False,
        'checklist': [],
        'status': {}
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        key_values = list(value.keys())
        key_schema = list(o['key'] for o in self.checklist)
        unused_keys = copy(key_schema)

        for k in key_values:
            if k not in key_schema:
                raise FieldError((
                    "Answer Key '{0}' is not a valid"
                    " option for this form.").format(k))
            else:
                unused_keys.remove(k)
                if not isinstance(value[k], bool):
                    raise FieldError((
                        "'{0}': Expected boolean, got '{1}'").format(
                            k, type(value[k]).__name__ 
                        ))

        if len(unused_keys) > 0:
            raise FieldError((
                    "The following keys are missing from the answer:"
                    "{0}").format(unused_keys))

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('inspection', InspectionField)
