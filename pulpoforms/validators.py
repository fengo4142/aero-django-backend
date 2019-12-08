"""
Validation Classes
"""

from pulpoforms.factories import ValidatorFactory
from pulpoforms.exceptions import ValidationError, FieldError


class BaseValidator:
    """ Default abstract validator type class """
    VALIDATOR_KEYS = ['type', 'value']

    def __init__(self, dictionary, field):
        self.validate_schema(dictionary)
        self.field_allows_validator(field)
        self.check_value(dictionary['value'])
        for k, v in dictionary.items():
            setattr(self, k, v)

    @classmethod
    def validate_schema(cls, validator):
        errors = []
        expected_keys = list(cls.VALIDATOR_KEYS)
        for key in validator:
            try:
                expected_keys.remove(key)
            except ValueError:
                errors.append(
                    ("Key '{0}' either doesn't belong in the schema or"
                     " is duplicated").format(key))
                continue

        for key in expected_keys:
            errors.append("Required key '{0}' missing from the schema".format(
                key))

        if errors:
            raise ValidationError(errors)

    @classmethod
    def field_allows_validator(cls, field):
        if cls.VALIDATOR_KEY not in field.allowed_validators:
            raise ValidationError(
                ("Field '{0}' of type '{1}' does not accept the '{2}' "
                 "validator type").format(
                    field.id, field.type, cls.VALIDATOR_KEY))

    def check_value(self, value):
        pass

    def validate(self, field):
        pass

    class Meta:
        abstract = True


class MinLength(BaseValidator):
    """ Validator type that checks if a field is long enough """
    VALIDATOR_NAME = 'min length'
    VALIDATOR_KEY = 'minLength'

    DEFAULT_SCHEMA = {
        'type': 'minLength',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                "Min Length value must be an 'integer', got '{0}'".format(
                    type(value).__name__))

    def validate(self, field):
        if len(field) < int(self.value):
            raise FieldError({
                'id': 'section1.errors.min_length',
                'values': {
                    'min': self.value,
                    'answer': len(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('minLength', MinLength)


class MaxLength(BaseValidator):
    """ Validator type that checks if a field is not too long """
    VALIDATOR_NAME = 'max length'
    VALIDATOR_KEY = 'maxLength'

    DEFAULT_SCHEMA = {
        'type': 'maxLength',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Max Length validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        if len(field) > int(self.value):
            raise FieldError({
                'id': 'section1.errors.max_length',
                'values': {
                    'max': self.value,
                    'answer': len(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('maxLength', MaxLength)


class MinChoices(BaseValidator):
    """Validator type that checks if a multiselect answer is long enough."""

    VALIDATOR_NAME = 'min choices'
    VALIDATOR_KEY = 'minChoices'

    DEFAULT_SCHEMA = {
        'type': 'minChoices',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                "Min Choices value must be an 'integer', got '{0}'".format(
                    type(value).__name__))

    def validate(self, field):
        if len(field) < int(self.value):
            raise FieldError({
                'id': 'section1.errors.min_choices',
                'values': {
                    'min': self.value,
                    'answer': len(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('minChoices', MinChoices)


class MaxChoices(BaseValidator):
    """Validator type that checks if a multiselect answer is not too long."""

    VALIDATOR_NAME = 'max choices'
    VALIDATOR_KEY = 'maxChoices'

    DEFAULT_SCHEMA = {
        'type': 'maxChoices',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Max Choices validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        if len(field) > int(self.value):
            raise FieldError({
                'id': 'section1.errors.max_choices',
                'values': {
                    'max': self.value,
                    'answer': len(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('maxChoices', MaxChoices)


class Contains(BaseValidator):
    """ Validator type that checks if a field contains some value """
    VALIDATOR_NAME = 'contains'
    VALIDATOR_KEY = 'contains'

    DEFAULT_SCHEMA = {
        'type': 'contains',
        'value': '',
    }

    def check_value(self, value):
        if not isinstance('value', str):
            raise ValidationError(
                "Value for Contains validator must be 'string', got '{0}'"
                .format(type(value).__name__))

    def validate(self, field):
        if self.value not in field:
            raise FieldError({
                'id': 'section1.errors.contains',
                'values': {
                    'word': self.value
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('contains', Contains)


class MinValue(BaseValidator):
    """ Validator type that checks if a field's value is enough """
    VALIDATOR_NAME = 'min value'
    VALIDATOR_KEY = 'minValue'

    DEFAULT_SCHEMA = {
        'type': 'minValue',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Min Value validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        if int(field) < int(self.value):
            raise FieldError({
                'id': 'section1.errors.min_value',
                'values': {
                    'min': self.value,
                    'answer': int(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('minValue', MinValue)


class MaxValue(BaseValidator):
    """ Validator type that checks if a field's value is not too much """
    VALIDATOR_NAME = 'max value'
    VALIDATOR_KEY = 'maxValue'

    DEFAULT_SCHEMA = {
        'type': 'maxValue',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Max Value validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        if int(field) > int(self.value):
            raise FieldError({
                'id': 'section1.errors.max_value',
                'values': {
                    'max': self.value,
                    'answer': int(field)
                }
            })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('maxValue', MaxValue)


class RankMinValue(BaseValidator):
    """
    Validator type that checks if a field's value is enough.

    Will check that none of the values given for the rank options is less
    than the set minimum.
    """

    VALIDATOR_NAME = 'min value'
    VALIDATOR_KEY = 'rankMinValue'

    DEFAULT_SCHEMA = {
        'type': 'rankMinValue',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Min Value validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        for _, value in field.items():
            if isinstance(value, dict):
                # In case field type is Rank Other
                value = value['value']
            if value is not None and int(value) < int(self.value):
                raise FieldError({
                    'id': 'section1.errors.rank_field.min_value',
                    'values': {
                        'min': self.value,
                        'answer': int(value)
                    }
                })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('rankMinValue', RankMinValue)


class RankMaxValue(BaseValidator):
    """
    Validator type that checks if a Rank field's value is not too much.

    Will check that none of the values given for the rank options is greater
    than the set maximum.
    """

    VALIDATOR_NAME = 'max value'
    VALIDATOR_KEY = 'rankMaxValue'

    DEFAULT_SCHEMA = {
        'type': 'rankMaxValue',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                ("Value for Max Value validator must be 'integer', "
                 "got '{0}'").format(type(value).__name__))

    def validate(self, field):
        for _, value in field.items():
            if isinstance(value, dict):
                # In case field type is Rank Other
                value = value['value']
            if value is not None and int(value) > int(self.value):
                raise FieldError({
                    'id': 'section1.errors.rank_field.max_value',
                    'values': {
                        'max': self.value,
                        'answer': int(value)
                    }
                })

    def __str__(self):
        return self.__name__

ValidatorFactory.register('rankMaxValue', RankMaxValue)


class MaxSize(BaseValidator):
    """ Validator type that checks if a field's size is not too large """
    VALIDATOR_NAME = 'max size'
    VALIDATOR_KEY = 'maxSize'

    DEFAULT_SCHEMA = {
        'type': 'maxSize',
        'value': '',
    }

    def check_value(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(
                "Value for Max Size validator must be 'integer', got '{0}'"
                .format(type(value).__name__))

    def __str__(self):
        return self.__name__

ValidatorFactory.register('maxSize', MaxSize)


class FileTypes(BaseValidator):
    """
    Validator type that checks if a field type belongs in the allowed list.
    """
    VALIDATOR_NAME = 'allowed file types'
    VALIDATOR_KEY = 'fileTypes'

    DEFAULT_SCHEMA = {
        'type': 'fileTypes',
        'value': [],
    }

    def check_value(self, value):
        if not isinstance(value, list):
            raise ValidationError(
                "Value for File Types validator must be 'list', got '{0}'"
                .format(type(value).__name__))

    def __str__(self):
        return self.__name__

ValidatorFactory.register('fileTypes', FileTypes)
