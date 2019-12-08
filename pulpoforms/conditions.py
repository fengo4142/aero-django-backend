"""
Condition Classes
"""

import re

from pulpoforms.factories import ConditionFactory
from pulpoforms.exceptions import ConditionError


class Condition:
    """ Default abstract condition type class """

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)

    @classmethod
    def check_condition(cls, condition):
        compound = False
        errors = []
        try:
            if (condition['type'] == 'all' or
                    condition['type'] == 'any'):
                compound_fields = ['state', 'conditionList']
                compound = True
        except KeyError:
            errors.append("Conditional must have a 'type' property.")

        if compound:
            for compound_field in compound_fields:
                try:
                    condition[compound_field]
                except KeyError:
                    errors.append(
                        "Missing required key "
                        "'{0}' in compound condition".format(
                            compound_field))
                    continue
            try:
                condition_list = condition['conditionList']
            except KeyError:
                # We pass because it was already checked
                pass
        else:
            condition_list = [condition]

        if errors:
            raise ConditionError(errors)
        return condition_list, compound

    @classmethod
    def validate_schema(cls, condition, compound=False):
        expected_keys = list(cls.EXPECTED_KEYS)
        if not compound:
            expected_keys.append('state')
        errors = []
        for key in condition:
            try:
                expected_keys.remove(key)
            except ValueError:
                errors.append(
                    ("Key '{0}' either doesn't belong in the '{1}' "
                     "condition schema or is duplicated").format(
                        key, condition['type']))
        for key in expected_keys:
            errors.append(
                ("Required key '{0}' missing from '{1}' condition schema")
                .format(key, condition['type']))

        if compound and 'state' in condition:
            errors.append((
                "Key 'state' in '{0}' condition can't be present in the " +
                "clauses of compund conditions.").format(
                    condition['type']))
        elif (not compound and 'state' in condition and
                not isinstance(condition['state'], dict)):
            errors.append(
                "Key 'state' must be a dictionary, got '{0}'.".format(
                    type(condition['state']).__name__))

        if errors:
                raise ConditionError(errors)

    @classmethod
    def field_allows_condition(cls, field):
        if cls.CONDITION_KEY not in field.allowed_conditions:
            raise ConditionError(
                ("Field '{0}' of type '{1}' does not accept the '{2}' "
                 "condition type").format(
                    field.id, field.type, cls.CONDITION_KEY))

    @classmethod
    def get_condition_result(cls, results, condition_type):
        if condition_type == 'all':
            result = True
            for r in results:
                result = result and r
            return result
        elif condition_type == 'any':
            result = False
            for r in results:
                result = result or r
            return result
        else:
            return results[0]

    def eval_condition(self, value):
        return True

    class Meta:
        abstract = True


class Empty(Condition):
    """ Condition type that checks if a field is empty """
    CONDITION_NAME = 'empty'
    CONDITION_KEY = 'empty'
    EXPECTED_KEYS = [
        'type', 'field'
    ]

    DEFAULT_SCHEMA = {
        'type': 'empty',
        'field': ''
    }

    def eval_condition(self, value):
        if isinstance(value, list):
            return len(value) == 0
        return (value is None or value == '')

    def __str__(self):
        return self.__name__

ConditionFactory.register('empty', Empty)


class NotEmpty(Condition):
    """ Condition type that checks if a field is not empty """
    CONDITION_NAME = 'not empty'
    CONDITION_KEY = 'notEmpty'
    EXPECTED_KEYS = [
        'type', 'field'
    ]

    DEFAULT_SCHEMA = {
        'type': 'notEmpty',
        'field': ''
    }

    def eval_condition(self, value):
        if isinstance(value, list):
            return len(value) != 0
        return (value is not None and value != '')

    def __str__(self):
        return self.__name__

ConditionFactory.register('notEmpty', NotEmpty)


class Equals(Condition):
    """Condition type that checks if a field is equal to some value."""

    CONDITION_NAME = 'equals'
    CONDITION_KEY = 'equals'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'equals',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if isinstance(value, list):
            # Multiple values selected will never be equal to one value
            if len(value) > 1:
                return False
            else:
                return self.value in value
        if isinstance(value, dict):
            try:
                value = value['option']
            except KeyError:
                value = value['value']

        return value == self.value or str(value) == str(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('equals', Equals)


class NotEquals(Condition):
    """Condition type that checks if a field is not equal to some value."""

    CONDITION_NAME = 'not equals'
    CONDITION_KEY = 'notEquals'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'notEquals',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return True
        else:
            # Check for multiselect answer
            if isinstance(value, list):
                # Multiple values selected will never be equal to one value
                if len(value) > 1:
                    return True
                else:
                    return self.value not in value
            if isinstance(value, dict):
                try:
                    value = value['option']
                except KeyError:
                    value = value['value']
            return str(value) != str(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('notEquals', NotEquals)


class Contains(Condition):
    """ Condition type that checks if a field contains some value """
    CONDITION_NAME = 'contains'
    CONDITION_KEY = 'contains'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'contains',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        if isinstance(value, list):
            return str(self.value) in map(str, value)
        return self.value in value

    def __str__(self):
        return self.__name__

ConditionFactory.register('contains', Contains)


class NotContains(Condition):
    """Condition type that checks if a field does not contain some value."""

    CONDITION_NAME = 'does not contain'
    CONDITION_KEY = 'notContains'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'notContains',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return True
        if isinstance(value, list):
            return str(self.value) not in map(str, value)
        return self.value not in value

    def __str__(self):
        return self.__name__

ConditionFactory.register('notContains', NotContains)


class StartsWith(Condition):
    """ Condition type that checks if a field starts with some value """
    CONDITION_NAME = 'starts with'
    CONDITION_KEY = 'startsWith'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'startsWith',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        expr = re.compile('^' + self.value + '.*', re.IGNORECASE)
        matches = expr.match(value)
        if matches:
            return True
        return False

    def __str__(self):
        return self.__name__

ConditionFactory.register('startsWith', StartsWith)


class NotStartsWith(Condition):
    """ Condition type that checks if a field does not start with some value """
    CONDITION_NAME = 'does not start with'
    CONDITION_KEY = 'notStartsWith'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'notStartsWith',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return True
        expr = re.compile('^' + self.value + '.*', re.IGNORECASE)
        matches = expr.match(value)
        if not matches:
            return True
        return False

    def __str__(self):
        return self.__name__

ConditionFactory.register('notStartsWith', NotStartsWith)


class EndsWith(Condition):
    """ Condition type that checks if a field ends with some value """
    CONDITION_NAME = 'ends with'
    CONDITION_KEY = 'endsWith'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'endsWith',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        expr = re.compile('.*' + self.value + '$', re.IGNORECASE)
        matches = expr.match(value)
        if matches:
            return True
        return False

    def __str__(self):
        return self.__name__

ConditionFactory.register('endsWith', EndsWith)


class NotEndsWith(Condition):
    """ Condition type that checks if a field does not end with some value """
    CONDITION_NAME = 'does not end with'
    CONDITION_KEY = 'notEndsWith'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'notEndsWith',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return True
        expr = re.compile('.*' + self.value + '$', re.IGNORECASE)
        matches = expr.match(value)
        if not matches:
            return True
        return False

    def __str__(self):
        return self.__name__

ConditionFactory.register('notEndsWith', NotEndsWith)


class Greater(Condition):
    """ Condition type that checks if a field is greater than some value """
    CONDITION_NAME = 'greater than'
    CONDITION_KEY = 'greater'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'greater',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        else:
            return value > int(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('greater', Greater)


class GreaterEqual(Condition):
    """
    Condition type that checks if a field is greater than or equal to some
    value
    """
    CONDITION_NAME = 'greater than or equal to'
    CONDITION_KEY = 'greaterEqual'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'greaterEqual',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        else:
            return value >= int(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('greaterEqual', GreaterEqual)


class LesserEqual(Condition):
    """
    Condition type that checks if a field is lesser than or equal to some value
    """
    CONDITION_NAME = 'less than or equal to'
    CONDITION_KEY = 'lesserEqual'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'lesserEqual',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        else:
            return value <= int(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('lesserEqual', LesserEqual)


class Lesser(Condition):
    """
    Condition type that checks if a field is lesser than some value
    """
    CONDITION_NAME = 'less than'
    CONDITION_KEY = 'lesser'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'lesser',
        'field': '',
        'value': ''
    }

    def eval_condition(self, value):
        if value is None:
            return False
        else:
            return value < int(self.value)

    def __str__(self):
        return self.__name__

ConditionFactory.register('lesser', Lesser)


class Before(Condition):
    """ Condition type that checks if a field is before some value """
    CONDITION_NAME = 'before'
    CONDITION_KEY = 'before'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'before',
        'field': '',
        'value': ''
    }

    def __str__(self):
        return self.__name__

ConditionFactory.register('before', Before)


class After(Condition):
    """ Condition type that checks if a field is after some value """
    CONDITION_NAME = 'after'
    CONDITION_KEY = 'after'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'after',
        'field': '',
        'value': ''
    }

    def __str__(self):
        return self.__name__

ConditionFactory.register('after', After)


class MaxDistanceTo(Condition):
    """
    Condition type that checks if field is at a max distance to some value
    """
    CONDITION_NAME = 'max distance to'
    CONDITION_KEY = 'maxDistanceTo'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'maxDistanceTo',
        'field': '',
        'value': ''
    }

    def __str__(self):
        return self.__name__

ConditionFactory.register('maxDistanceTo', MaxDistanceTo)


class MinDistanceTo(Condition):
    """
    Condition type that checks if field is at a min distance to some value
    """
    CONDITION_NAME = 'min distance to'
    CONDITION_KEY = 'minDistanceTo'
    EXPECTED_KEYS = [
        'type', 'field', 'value'
    ]

    DEFAULT_SCHEMA = {
        'type': 'minDistanceTo',
        'field': '',
        'value': ''
    }

    def __str__(self):
        return self.__name__

ConditionFactory.register('minDistanceTo', MinDistanceTo)


class RankCondition(Condition):
    """Condition type for Rank and RankOther fields."""

    CONDITION_NAME = 'rank options condition'
    CONDITION_KEY = 'rankCondition'
    EXPECTED_KEYS = [
        'type', 'field', 'clauses'
    ]

    DEFAULT_SCHEMA = {
        'type': 'rankCondition',
        'field': '',
        'clauses': []
    }

    def eval_condition(self, value):
        result = True
        for clause in self.clauses:
            condition_class = ConditionFactory.get_class(clause['operator'])
            try:
                option_value = value.get(str(clause['option']))
            except AttributeError:
                option_value = None
            cond_obj = condition_class({'value': clause['value']})
            result &= cond_obj.eval_condition(option_value)

        return result

    def __str__(self):
        return self.__name__

ConditionFactory.register('rankCondition', RankCondition)
