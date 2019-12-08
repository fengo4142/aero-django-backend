"""Field Classes."""

import re
from math import floor
from copy import copy
import logging

from pulpoforms.exceptions import FieldError, ConditionError, ValidationError
from pulpoforms.factories import ConditionFactory, ValidatorFactory, \
    FieldFactory

logger = logging.getLogger('pulpo_forms')


class Field:
    """Default abstract field type class."""

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required'
    ]
    OPTIONAL_KEYS = [
        'conditionals', 'widget', 'validators', 'tooltip', 'hidden',
        'default'
    ]

    def __init__(self, dictionary):
        self.validate_schema(dictionary)
        self.validation_classes = []
        for k, v in dictionary.items():
            setattr(self, k, v)
        if 'validators' in dictionary:
            self.check_validators(dictionary['validators'])
        if 'widget' in dictionary:
            self.check_widget(dictionary['widget'])

    def check_validators(self, validators, **kwargs):
        errors = []
        for validator in validators:
            try:
                validator_class = ValidatorFactory.get_class(validator['type'])
            except KeyError:
                errors.append("Invalid validator type: '{0}'".format(
                    validator['type']))
                continue
            try:
                validator_obj = validator_class(validator, self)
                self.validation_classes.append(validator_obj)
            except ValidationError as e:
                errors = []
                for err in e:
                    errors.append(str(err))
                raise FieldError(errors)

    def check_widget(self, widget):
        if not isinstance(widget, dict):
            raise FieldError(
                "Invalid 'widget' definition, expected 'dictionary', got '{0}'"
                .format(type(widget).__name__))
        try:
            if widget['type'] not in self.allowed_widgets:
                raise FieldError(
                    ("Field '{0}' of type '{1}' does not accept the '{2}' "
                     "widget type").format(
                        self.id, self.type, widget['type']))
        except KeyError:
            raise FieldError("Invalid 'widget' definition")

    @classmethod
    def validate_schema(cls, field):
        errors = []
        expected_keys = list(cls.EXPECTED_KEYS)
        optional_keys = list(cls.OPTIONAL_KEYS)
        for key in field:
            if key in expected_keys:
                expected_keys.remove(key)
            else:
                try:
                    optional_keys.remove(key)
                except ValueError:
                    errors.append(
                        "Key '{0}' either doesn't belong in the field schema "
                        "or is duplicated".format(key))

        for key in expected_keys:
            errors.append(
                "Required key '{0}' is missing from the field schema".format(
                    key))

        if errors:
            raise FieldError(errors)

    @classmethod
    def register_condition(cls, key):
        try:
            ConditionFactory.get_class(key)
        except KeyError:
            raise ConditionError(
                "Condition with key '{0}' does not exist".format(key))
        cls.allowed_conditions.add(key)

    @classmethod
    def register_validator(cls, key):
        try:
            ValidatorFactory.get_class(key)
        except KeyError:
            raise ValidationError(
                "Validator with key '{0}' does not exist".format(key))
        cls.allowed_validators.add(key)

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        pass

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        pass

    def get_statistic_template(self):
        # Return template where the statistical information for the field
        # will be gathered
        return None, False

    class Meta:
        abstract = True


class ListField(Field):
    """
    Abstract field type for lists.

    Handles validation of this field type schema and entries.
    """

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required', 'values'
    ]
    OPTIONAL_KEYS = [
        'conditionals', 'widget', 'validators', 'tooltip', 'hidden',
        'default'
    ]

    def __init__(self, dictionary):
        super(ListField, self).__init__(dictionary)
        self.option_values = []
        for value in self.values:
            self.option_values.append(value['key'])

    @classmethod
    def validate_schema(cls, field):
        errors = []
        expected_keys = list(cls.EXPECTED_KEYS)
        optional_keys = list(cls.OPTIONAL_KEYS)
        for key in field:
            if key in expected_keys:
                expected_keys.remove(key)
            else:
                try:
                    optional_keys.remove(key)
                except ValueError:
                    errors.append(
                        "Key '{0}' either doesn't belong in the field schema "
                        "or is duplicated".format(key))

        for key in expected_keys:
            errors.append(
                "Required key '{0}' is missing from the field schema".format(
                    key))

        if errors:
            raise FieldError(errors)

        if not isinstance(field['values'], list):
            errors.append("'values' property must be a list")
            raise FieldError(errors)

        for value in field['values']:
            if not isinstance(value, dict):
                errors.append(
                    "Every element of 'values' property must be a dictionary")
                continue
            expected_values_keys = ['key', 'value']
            for key in value:
                if key in expected_values_keys:
                    expected_values_keys.remove(key)
                else:
                    errors.append(
                        "Key '{0}' doesn't belong in field values "
                        "schema".format(key))

            for key in expected_values_keys:
                errors.append(
                    "Required key '{0}' missing in field values "
                    "schema".format(key))

        if errors:
            raise FieldError(errors)

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        stat_template['options'][value]['count'] += 1
        stat_template['count'] += 1

        return stat_template

    def post_process_data(self, stat_template):
        options = []
        for option in self.values:
            options.append(stat_template['options'][option['key']])

        stat_template['options'] = options

    def get_statistic_template(self):
        template = {}
        template['options'] = {}
        template['count'] = 0
        for option in self.values:
            opt = {
                'value': option['value'],
                'count': 0
            }
            template['options'].update({option['key']: opt})

        return template, True

    class Meta:
        abstract = True


class StringField(Field):
    """
    Field type for strings.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'startsWith',
         'notStartsWith', 'endsWith', 'notEndsWith', 'contains', 'notContains']
    )
    allowed_validators = set(
        ['minLength', 'maxLength', 'contains']
    )
    allowed_widgets = set(
        ['charfield', 'textfield']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'string',
        'title': '',
        'required': False,
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('string', StringField)


class EmailField(StringField):
    """
    Field type for emails.

    Handles validation of this field type schema and entries
    """

    EMAIL_RE = r'^[^@]+@[^@]+$'
    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'startsWith',
         'notStartsWith', 'endsWith', 'notEndsWith', 'contains', 'notContains']
    )

    allowed_validators = set(
        ['minLength', 'maxLength', 'contains']
    )

    allowed_widgets = set(
        ['charfield']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'email',
        'title': '',
        'required': False,
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        if not re.match(self.EMAIL_RE, value):
            raise FieldError({
                'id': 'section1.errors.invalid_email',
                'values': {
                    'answer': value
                }
            })

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('email', EmailField)


class BooleanField(Field):
    """
    Field type for select fields.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals']
    )
    allowed_validators = set(
        []
    )
    allowed_widgets = set(
        ['radio', 'dropdown', 'checkbox']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'boolean',
        'title': '',
        'required': False,
    }

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        if value:
            stat_template['true'] += 1
        else:
            stat_template['false'] += 1

        return stat_template

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        if not isinstance(value, bool):
            raise FieldError(
                "Expected boolean value, got '{0}'".format(
                    type(value).__name__))

    def get_statistic_template(self):
        return {'true': 0, 'false': 0, 'count': 0}, False

FieldFactory.register('boolean', BooleanField)


class NumberField(Field):
    """
    Field type for numbers.

    Handles validation of this field type schema and entries
    """

    OPTIONAL_KEYS = [
        'conditionals', 'widget', 'validators', 'tooltip', 'hidden',
        'default', 'decimals', 'prefix', 'suffix'
    ]

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'greater', 'greaterEqual',
         'lesserEqual', 'lesser']
    )

    allowed_validators = set(
        ['minValue', 'maxValue']
    )

    allowed_widgets = set(
        ['numberfield']
        # , 'slider']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'number',
        'title': '',
        'required': False,
    }

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        stat_template['values'].append(value)

        return stat_template

    def post_process_data(self, stat_template):
        partitions = []

        values_list = stat_template['values']
        try:
            min_item = min(values_list)
        except ValueError:
            stat_template['values'] = partitions
            return stat_template['values']
        max_item = max(values_list)
        partition_size = floor((max_item - min_item + 1) / 5)

        initial = min_item
        for _ in range(1, 5):
            final = initial + partition_size
            partition = {
                'initial': initial,
                'final': final,
                'count': 0
            }
            partitions.append(copy(partition))
            initial = final + 1

        partition = {
            'initial': initial,
            'final': max_item,
            'count': 0
        }
        partitions.append(copy(partition))

        for value in values_list:
            if partitions[0]['initial'] <= value <= partitions[0]['final']:
                partitions[0]['count'] += 1

            elif partitions[1]['initial'] <= value <= partitions[1]['final']:
                partitions[1]['count'] += 1

            elif partitions[2]['initial'] <= value <= partitions[2]['final']:
                partitions[2]['count'] += 1

            elif partitions[3]['initial'] <= value <= partitions[3]['final']:
                partitions[3]['count'] += 1

            elif partitions[4]['initial'] <= value <= partitions[4]['final']:
                partitions[4]['count'] += 1

        stat_template['values'] = partitions
        return stat_template['values']

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        try:
            float_value = float(value)
        except ValueError:
            raise FieldError("'{0}' is not a number".format(value))

        try:
            self.decimals
        except AttributeError:
            self.decimals = False

        if not self.decimals and not float_value.is_integer():
            raise FieldError({
                'id': 'section1.errors.only_integer',
                'values': {
                    'answer': value
                }
            })

        for validator in self.validation_classes:
            validator.validate(value)

    def get_statistic_template(self):
        return {'values': []}, True


FieldFactory.register('number', NumberField)


class SelectField(ListField):
    """
    Field type for select fields.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals']
    )

    allowed_validators = set(
        []
    )

    allowed_widgets = set(
        ['radio', 'dropdown']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'select',
        'title': '',
        'required': False,
        'values': []
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        if value not in self.option_values:
            raise FieldError(
                "'{0}' is not a a correct option value".format(value))
        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('select', SelectField)


class SelectWithOtherField(ListField):
    """
    Field type for select fields with an additional 'Other' option.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals']
    )

    allowed_validators = set(
        []
    )

    allowed_widgets = set(
        []
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'select_other',
        'title': '',
        'required': False,
        'values': [{'key': 'OTHER', 'value': 'Other'}]
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        if 'option' in value and value['option'] not in self.option_values:
            raise FieldError(
                "'{0}' is not a a correct option value".format(value))
        if ('option' in value and
                value['option'] == 'OTHER' and not value['answer']):
            raise FieldError({
                'id': 'section1.errors.other_option',
            })

        for validator in self.validation_classes:
            validator.validate(value)

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        stat_template['options'][value['option']]['count'] += 1
        stat_template['count'] += 1

        return stat_template


FieldFactory.register('select_other', SelectWithOtherField)


class MultiselectField(ListField):
    """
    Field type for select fields.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'contains', 'notContains']
    )

    allowed_validators = set(
        ['minChoices', 'maxChoices']
    )

    allowed_widgets = set(
        ['checkbox']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'multiselect',
        'title': '',
        'required': False,
        'values': []
    }

    @classmethod
    def add_statistic_data(cls, stat_template, value):
        for v in value:
            stat_template['options'][v]['count'] += 1
            stat_template['count'] += 1

        return stat_template

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        invalid_values = []
        for v in value:
            if v not in self.option_values:
                invalid_values.append(
                    "'{0}' is not a a correct option value".format(v))
        if invalid_values:
            raise FieldError(invalid_values)

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('multiselect', MultiselectField)


class DateField(Field):
    """
    Field type for dates.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'before', 'after']
    )

    allowed_validators = set(
        ['minValue', 'maxValue']
    )

    allowed_widgets = set(
        ['calendar', 'datepicker']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'date',
        'title': '',
        'required': False,
    }


FieldFactory.register('date', DateField)


class DatetimeField(Field):
    """
    Field type for datetime fields.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'before', 'after']
    )

    allowed_validators = set(
        ['minValue', 'maxValue']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'datetime',
        'title': '',
        'required': False,
    }


FieldFactory.register('datetime', DatetimeField)


class DurationField(Field):
    """
    Field type for dates.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'greater', 'greaterEqual',
         'lesserEqual', 'lesser']
    )

    allowed_validators = set(
        ['minValue', 'maxValue']
    )

    allowed_widgets = set(
        ['numberfield', 'slider']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'duration',
        'title': '',
        'required': False,
    }

# FieldFactory.register('duration', DurationField)


class TimeField(Field):
    """
    Field type for time.

    Handles validation of this field type schema and entries
    """

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'before', 'after']
    )

    allowed_validators = set(
        ['minValue', 'maxValue']
    )

    allowed_widgets = set(
        ['numberfield', 'slider']
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'time',
        'title': '',
        'required': False,
        'values': []
    }

# FieldFactory.register('time', TimeField)


class RankField(ListField):
    """
    Field type for Rank fields.

    Handles validation of this field type schema and entries
    """

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required', 'values', 'sum_total'
    ]

    OPTIONAL_KEYS = [
        'conditionals', 'widget', 'validators', 'tooltip', 'hidden',
        'default', 'decimals'
    ]

    allowed_conditions = set(
        ['rankCondition']
    )

    allowed_validators = set(
        ['rankMinValue', 'rankMaxValue']
    )

    allowed_widgets = set(
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'rank',
        'title': '',
        'required': False,
        'values': []
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        try:
            self.decimals
        except AttributeError:
            self.decimals = False

        invalid_values = []
        sum = 0
        for option in value.keys():
            str_option_values = [str(x) for x in self.option_values]
            if option not in str_option_values:
                invalid_values.append(
                    "'{0}' is not a a correct option value".format(option))
            if value[option]:
                try:
                    float_value = float(value[option])
                except ValueError:
                    invalid_values.append(
                        "Answer for option '{0}' must be a number".format(
                            option))
                    continue
                if not self.decimals and not float_value.is_integer():
                    invalid_values.append({
                        'id': 'section1.errors.rank_field.only_integer',
                        'values': {
                            'option': option
                        }
                    })

                sum += float_value

        if invalid_values:
            raise FieldError(invalid_values)

        if sum != self.sum_total:
            raise FieldError({
                'id': 'section1.errors.rank_field.add',
                'values': {
                    'total': self.sum_total
                }
            })

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('rank', RankField)


class RankWithOtherField(ListField):
    """
    Field type for Rank With Other fields.

    Handles validation of this field type schema and entries
    """

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required', 'values', 'sum_total'
    ]

    OPTIONAL_KEYS = [
        'conditionals', 'widget', 'validators', 'tooltip', 'hidden',
        'default', 'decimals'
    ]

    allowed_conditions = set(
        ['rankCondition']
    )

    allowed_validators = set(
        ['rankMinValue', 'rankMaxValue']
    )

    allowed_widgets = set(
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'rank_other',
        'title': '',
        'required': False,
        'values': [{'key': 'OTHER', 'value': 'Other'}]
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        try:
            self.decimals
        except AttributeError:
            self.decimals = False

        invalid_values = []
        sum = 0
        for option in value.keys():
            str_option_values = [str(x) for x in self.option_values]
            if option not in str_option_values:
                invalid_values.append(
                    "'{0}' is not a a correct option value".format(option))

            if option != 'OTHER' and value[option]:
                try:
                    float_value = float(value[option])
                except ValueError:
                    invalid_values.append(
                        "Answer for option '{0}' must be a number".format(
                            option))
                    continue
                if not self.decimals and not float_value.is_integer():
                    invalid_values.append({
                        'id': 'section1.errors.rank_field.only_integer',
                        'values': {
                            'option': option
                        }
                    })
                    continue

                sum += float_value

            if (option == 'OTHER' and 'value' in value[option] and
               value[option]['value']):
                try:
                    float_value = float(value[option]['value'])
                except ValueError:
                    invalid_values.append(
                        "Answer for option '{0}' must be a number".format(
                            option))
                    continue
                if not self.decimals and not float_value.is_integer():
                    invalid_values.append({
                        'id': 'section1.errors.rank_field.only_integer',
                        'values': {
                            'option': option
                        }
                    })
                    continue

                sum += float_value

                if ('new_option' not in value[option] or
                   not value['OTHER']['new_option']):
                    invalid_values.append({
                        'id': 'section1.errors.other_option',
                    })

        if invalid_values:
            raise FieldError(invalid_values)

        if sum != self.sum_total:
            raise FieldError({
                'id': 'section1.errors.rank_field.add',
                'values': {
                    'total': self.sum_total
                }
            })

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('rank_other', RankWithOtherField)


class SliderField(Field):
    """
    Field type for numbers.

    Handles validation of this field type schema and entries
    """

    EXPECTED_KEYS = [
        'type', 'id', 'title', 'required', 'max_value', 'min_value',
        'step'
    ]

    allowed_conditions = set(
        ['empty', 'notEmpty', 'equals', 'notEquals', 'greater', 'greaterEqual',
         'lesserEqual', 'lesser']
    )

    allowed_validators = set(
    )

    allowed_widgets = set(
    )

    DEFAULT_SCHEMA = {
        'id': '',
        'type': 'slider',
        'title': '',
        'required': False,
    }

    def validate_value(self, value):
        # Check if the value for this field's answer is valid.
        try:
            float(value)
        except ValueError:
            raise FieldError("'{0}' is not a number".format(value))

        for validator in self.validation_classes:
            validator.validate(value)


FieldFactory.register('slider', SliderField)
