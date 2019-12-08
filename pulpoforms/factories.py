"""
Factory Classes
"""


class FieldFactory:
    """ Factory for Fields """
    fields = {}

    @classmethod
    def get_class(cls, field_id):
        if isinstance(field_id, str):
            return FieldFactory.fields[field_id]
        else:
            raise Exception(
                "Invalid field id. Expected 'str', got '{0}'.".format(
                    type(field_id).__name__))

    def get_all_classes():
        return FieldFactory.fields.values()

    @classmethod
    def register(cls, field_id, field_type):
        if field_id not in FieldFactory.fields:
            FieldFactory.fields[field_id] = field_type
        else:
            raise Exception(
                "Field with name '{0}' already registered".format(field_id))

    def get_fields_name():
        names = []
        for key in FieldFactory.fields:
            names.append(key.capitalize())
        names.sort()
        return names


class ConditionFactory:
    """ Factory for Conditions """
    conditions = {}

    @classmethod
    def get_class(cls, condition_id):
        if isinstance(condition_id, str):
            return ConditionFactory.conditions[condition_id]
        else:
            raise Exception(
                "Invalid condition id. Expected 'str', got '{0}'.".format(
                    type(condition_id).__name__))

    def get_all_classes():
        return ConditionFactory.conditions.values()

    @classmethod
    def register(cls, condition_id, condition_type):
        if condition_id not in ConditionFactory.conditions:
            ConditionFactory.conditions[condition_id] = condition_type
        else:
            raise Exception(
                "Condition with name '{0}' already registered".format(
                    condition_id))

    def get_conditions_name():
        names = {}
        for key in ConditionFactory.conditions:
            names[key] = ConditionFactory.conditions[key]().__str__()
        return names


class ValidatorFactory:
    """ Factory for Validators """
    validators = {}

    @classmethod
    def get_class(cls, validator_id):
        if isinstance(validator_id, str):
            return ValidatorFactory.validators[validator_id]
        else:
            raise Exception(
                "Invalid validator id. Expected 'str', got '{0}'.".format(
                    type(validator_id).__name__))

    def get_all_classes():
        return ValidatorFactory.validators.values()

    @classmethod
    def register(cls, validator_id, validator_type):
        if validator_id not in ValidatorFactory.validators:
            ValidatorFactory.validators[validator_id] = validator_type
        else:
            raise Exception(
                "Validator with name '{0}' already registered".format(
                    validator_id))

    def get_validators_name():
        names = {}
        for key in ValidatorFactory.validators:
            names[key] = ValidatorFactory.validators[key]().__str__()
        return names
