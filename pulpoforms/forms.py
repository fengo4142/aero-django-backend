"""
Form Classes
"""

from copy import copy

from pulpoforms.factories import FieldFactory, ConditionFactory
from pulpoforms.fields import Field
from pulpoforms.conditions import Condition
from pulpoforms.exceptions import FormatError, FieldError, \
    ConditionError
import logging

logger = logging.getLogger('backend')

class Form:
    """ Python object created from a valid schema. """
    MINIMUM_SCHEMA_KEYS = ['id', 'version', 'fields', 'sections', 'pages']

    MINIMUM_SECTION_KEYS = ['id', 'title', 'fields']
    OPTIONAL_SECTION_KEYS = ['hidden', 'conditionals', 'description']

    MINIMUM_PAGE_KEYS = ['id', 'title', 'sections']
    OPTIONAL_PAGE_KEYS = ['hidden', 'conditionals', 'description']

    def __init__(self, schema):
        """
        Will try to create a Form object from the provided schema. If the
        schema does not define a valid form, it will return a list of the
        found errors
        """
        self.schema = schema or {}
        self.fields = {}
        self.sections = {}
        self.pages = {}
        self.field_ids = []
        self.section_ids = []
        self.page_ids = []
        self._errors = None
        self.full_clean()

    def _add_error(self, error_type, error):
        if self._errors['result'] is None:
            self._errors['result'] = error_type
        if (self._errors['result'] == 'SCHEMA ERROR' and
                error_type == "FORMAT ERROR"):
            self._errors['errors'] = []
        elif (self._errors['result'] == 'FORMAT ERROR' and
                error_type == "SCHEMA ERROR"):
            return

        if isinstance(error, list):
            self._errors['errors'].extend(error)
        elif isinstance(error, dict):
            self._errors['errors'].append(error)

    def _validate_schema_format(self):
        """
        Checks the outer structure of the schema and makes sure all the
        expected keys are present
        """
        if not isinstance(self.schema, dict):
            raise FormatError(
                "Expected schema to be a dictionary, got '{0}'".format(
                    type(self.schema).__name__))
        schema_keys = list(self.MINIMUM_SCHEMA_KEYS)
        errors = []
        for key in self.schema:
            try:
                schema_keys.remove(key)
            except ValueError:
                errors.append(
                    "Key '{0}' either doesn't belong in the schema or is "
                    "duplicated".format(key))

        for key in schema_keys:
            errors.append(
                "Required key '{0}' is missing from the schema".format(key))

        if 'version' in self.schema:
            try:
                int(self.schema['version'])
            except ValueError:
                errors.append("Invalid version: '{0}' is not a number.".format(
                    self.schema['version']))

        if 'fields' in self.schema:
            if not isinstance(self.schema['fields'], list):
                errors.append("'fields' property must be a list.")

        if 'sections' in self.schema:
            if not isinstance(self.schema['sections'], list):
                errors.append("'sections' property must be a list.")

        if 'pages' in self.schema:
            if not isinstance(self.schema['pages'], list):
                errors.append("'pages' property must be a list.")

        if errors:
            raise FormatError(errors)

    def _validate_fields(self):
        """ Checks that the fields are valid in the schema """
        fields = self.schema['fields']
        self.fields = {}
        for field in fields:
            errors = False
            error = {
                'type': 'FIELD',
                'id': '',
                'message': ''
            }
            try:
                error['id'] = field['id']
            except KeyError:
                raise FormatError("A field is missing the 'id' property.")
            if 'type' in field:
                try:
                    field_class = FieldFactory.get_class(field['type'])
                except KeyError:
                    errors = True
                    error['message'] = "Invalid field type: '{0}'".format(
                        field['type'])
                    self._add_error("SCHEMA ERROR", copy(error))
                    continue
                except Exception as e:
                    error['message'] = \
                        "Invalid field: '{0}'".format(e.__str__())
                    self._add_error("SCHEMA ERROR", copy(error))
                    continue
            else:
                try:
                    Field.validate_schema(field)
                except FieldError as e:
                    for field_error in e.error_list:
                        error['message'] = repr(field_error)
                        self._add_error("SCHEMA ERROR", copy(error))
                    continue

            try:
                field_obj = field_class(field)
            except FieldError as e:
                errors = True
                for field_error in e.error_list:
                    error['message'] = repr(field_error)
                    self._add_error("SCHEMA ERROR", copy(error))

            if not errors:
                if field['id'] not in self.field_ids:
                    self.field_ids.append(field['id'])
                    self.fields.update({field['id'].__str__(): field_obj})
                else:
                    error['message'] = (
                        "Field '{0}' is defined more than once.".format(
                            field['id']))
                    self._add_error("SCHEMA ERROR", copy(error))

    def _validate_sections(self):
        """
        Checks that the sections are valid in the schema.
        Also checks that fields are used in only one section.
        """
        sections = self.schema['sections']
        self.sections = {}
        # Make local copy of the available fields
        field_ids = list(self.field_ids)
        for section in sections:
            field_list = {}
            section_keys = list(self.MINIMUM_SECTION_KEYS)
            optional_section_keys = list(self.OPTIONAL_SECTION_KEYS)
            error = {
                'id': '',
                'type': 'SECTION',
                'message': ''
            }
            try:
                error['id'] = section['id']
            except KeyError:
                raise FormatError("A section is missing the 'id' property.")

            if section['id'] not in self.section_ids:
                self.section_ids.append(section['id'])
            else:
                error['message'] = "Section '{0}' is defined more than once." \
                    .format(section['id'])
                self._add_error('SCHEMA ERROR', copy(error))

            for key in section:
                if key in section_keys:
                    section_keys.remove(key)
                else:
                    try:
                        optional_section_keys.remove(key)
                    except ValueError:
                        error['message'] = "Key '{0}' either doesn't belong" \
                            " in the section schema or is duplicated" \
                            .format(key)
                        self._add_error('SCHEMA ERROR', copy(error))

            for key in section_keys:
                error['message'] = \
                    "Required key '{0}' is missing from the section".format(
                        key)
                self._add_error('SCHEMA ERROR', copy(error))

            try:
                section_fields = section['fields']
                for field in section_fields:
                    try:
                        field_ids.remove(field)
                    except ValueError:
                        error['message'] = \
                            ("Field '{0}' either isn't valid or was already "
                             "included in a previous section".format(field))
                        self._add_error('SCHEMA ERROR', copy(error))
                        continue
                    field_list.update(
                        {field.__str__(): self.fields[field.__str__()]})

            except KeyError:  # Only to avoid exception.
                # We continue because it was already checked.
                continue
            new_section = Section(section)
            new_section.fields = field_list
            self.sections.update({section['id'].__str__(): new_section})

    def _validate_pages(self):
        """
        Checks that the pages are valid in the schema.
        Also checks that sections are used in only one page.
        """
        pages = self.schema['pages']
        section_ids = list(self.section_ids)
        for page in pages:
            section_list = {}
            page_keys = list(self.MINIMUM_PAGE_KEYS)
            optional_page_keys = list(self.OPTIONAL_PAGE_KEYS)
            error = {
                'id': '',
                'type': 'PAGE',
                'message': ''
            }
            try:
                error['id'] = page['id']
            except KeyError:
                raise FormatError("A page is missing the 'id' property.")

            if page['id'] not in self.page_ids:
                self.page_ids.append(page['id'])
            else:
                error['message'] = "Page '{0}' is defined more than once." \
                    .format(page['id'])
                self._add_error('SCHEMA ERROR', copy(error))

            for key in page:
                if key in page_keys:
                    page_keys.remove(key)
                else:
                    try:
                        optional_page_keys.remove(key)
                    except ValueError:
                        error['message'] = (
                            "Key '{0}' either doesn't belong in the page "
                            "schema or is duplicated".format(key))
                        self._add_error('SCHEMA ERROR', copy(error))

            for key in page_keys:
                error['message'] = \
                    "Required key '{0}' is missing from the page".format(
                        key)
                self._add_error('SCHEMA ERROR', copy(error))

            try:
                page_sections = page['sections']
                for section in page_sections:
                    try:
                        section_ids.remove(section)
                    except ValueError:
                        error['message'] = (
                            "Section '{0}' either isn't valid or was already "
                            "included in a previous page".format(section))
                        self._add_error('SCHEMA ERROR', copy(error))
                        continue
                    section_list.update(
                        {section.__str__(): self.sections[section.__str__()]})
            except KeyError:
                pass
            new_page = Page(page)
            new_page.sections = section_list
            self.pages.update({page['id'].__str__(): new_page})

    def _check_item_conditionals(self, item_type):
        error_type = {
            'fields': 'FIELD',
            'sections': 'SECTION',
            'pages': 'PAGE'
        }
        for item in self.schema[item_type]:
            if 'conditionals' in item:
                conditionals = item['conditionals']
                for condition in conditionals:
                    error = {
                        'id': item['id'],
                        'type': error_type[item_type],
                        'message': ''
                    }

                    try:
                        condition_list, compound = Condition.check_condition(
                            condition)
                    except ConditionError as e:
                        for condition_error in e.error_list:
                            error['message'] = repr(condition_error)
                            self._add_error("SCHEMA ERROR", copy(error))
                        continue

                    for individual_condition in condition_list:
                        try:
                            condition_class = ConditionFactory.get_class(
                                individual_condition['type'])
                        except KeyError:
                            error['message'] = \
                                "Invalid condition type: '{0}'".format(
                                    individual_condition['type'])
                            self._add_error("SCHEMA ERROR", copy(error))
                            continue
                        except Exception as e:
                            error['message'] = \
                                "Invalid condition: '{0}'".format(e.__str__())
                            self._add_error("SCHEMA ERROR", copy(error))
                            continue

                        try:
                            condition_class.validate_schema(
                                individual_condition, compound)
                            condition_field = self.fields[
                                individual_condition['field'].__str__()]
                            condition_class.field_allows_condition(
                                condition_field)
                        except ConditionError as e:
                            for condition_error in e.error_list:
                                error['message'] = repr(condition_error)
                                self._add_error("SCHEMA ERROR", copy(error))
                        except KeyError:
                            error['message'] = (
                                "Condition depends on invalid or undefined "
                                "field '{0}'".format(
                                    individual_condition['field']))
                            self._add_error("SCHEMA ERROR", copy(error))

    def _check_item_mappings(self, item_type):
        if item_type == 'fields':
            error_type = 'FIELD'
            ids = 'field_ids'
            maps_to = 'section'
        else:
            error_type = 'SECTION'
            ids = 'section_ids'
            maps_to = 'page'
        error = {
            'id': '',
            'type': error_type,
            'message': ''
        }
        try:
            form_item = getattr(self, maps_to + 's')
        except AttributeError as ex:
            raise Exception('Unexpected property access in Form: {0}'.format(
                ex.__str__()))
        used_ids = set()
        for item in form_item.values():
            used_ids = used_ids.union(set(getattr(item, item_type).keys()))

        all_items = set(map(str, getattr(self, ids)))
        diff = set(all_items).difference(used_ids)
        if diff:
            for d in diff:
                error['id'] = d
                error['message'] = (
                    "Item has not been mapped to any {0}".format(maps_to))
                self._add_error("SCHEMA ERROR", copy(error))

    def full_clean(self):
        """
        Performs a full clean of all the Form data and populates self._errors
        and self.cleaned_data
        """
        self._errors = {
            'result': None,
            'errors': []
        }
        try:
            self._validate_schema_format()
            self._validate_fields()
            self._validate_sections()
            self._validate_pages()
            self._check_item_conditionals('fields')
            self._check_item_conditionals('sections')
            self._check_item_conditionals('pages')
            self._check_item_mappings('fields'),
            self._check_item_mappings('sections'),
        except FormatError as e:
            self._add_error('FORMAT ERROR', e.error_list)

    @property
    def errors(self):
        """
        Inspired by Django's error management. If the Form has errors we return
        them.
        """
        return self._errors

    def check_answers(self, answers):
        if not isinstance(answers, dict):
            raise FormatError(
                "Expected answers to be a 'dictionary', got {0} instead"
                .format(type(answers).__name__))
                
        answer_keys = answers.keys()
        invalid_keys = []
        for key in answer_keys:
            try:
                self.fields[key.__str__()]
            except KeyError:
                invalid_keys.append(
                    "Field '{0}' does not match any field on the form."
                    .format(key))
                continue
        if invalid_keys:
            raise FieldError(invalid_keys)

        errors = []
        error = {
            'id': '',
            'message': {}
        }
        # We check for answers for each of the form's fields
        for key in self.fields:
            field = self.fields[key.__str__()]
            is_hidden, is_required = self.check_state(key, answers)
            try:
                answer = answers[key]
            except KeyError:
                if is_required and not is_hidden:
                    error['id'] = key
                    error['message'] = {
                        "id": "section1.errors.required_field"
                    }
                    errors.append(copy(error))
                continue
            # If the field is hidden we don't need the answer
            if is_hidden:
                del answers[key]
                continue
            # If there is no answer for a field we don't run validations
            if answer is None or answer == "":
                if is_required and not is_hidden:
                    error['id'] = key
                    error['message'] = {
                        "id": "section1.errors.required_field"
                    }
                    errors.append(copy(error))
            else:
                try:
                    field.validate_value(answer)
                except FieldError as err:
                    error['id'] = key
                    for e in err:
                        error['message'] = e
                        errors.append(copy(error))
        if errors:
            result = {
                'result': 'ANSWER_ERROR',
                'errors': errors
            }
            return result
        else:
            success = {}
            success['result'] = "OK"
            success['message'] = "The answer is valid."
            return success

    def check_state(self, field_id, answers):
        field = self.fields[field_id.__str__()]
        for sec in self.sections.values():
            if field_id in sec.fields.keys():
                section = sec
                break
        for p in self.pages.values():
            if section.id.__str__() in p.sections.keys():
                page = p
                break
        try:
            field_hidden = field.hidden
        except AttributeError:
            field_hidden = False
        try:
            section_hidden = section.hidden
        except AttributeError:
            section_hidden = False
        try:
            page_hidden = page.hidden
        except AttributeError:
            page_hidden = False

        try:
            field_required = field.required
        except AttributeError:
            field_required = False

        try:
            field_conditionals = field.conditionals
        except AttributeError:
            field_conditionals = []

        for conditional in field_conditionals:
            conditions, compound = Condition.check_condition(conditional)
            results = []
            for condition in conditions:
                condition_class = ConditionFactory.get_class(condition['type'])
                cond_obj = condition_class(condition)
                try:
                    cond_field = answers[cond_obj.field]
                except KeyError:
                    cond_field = None
                results.append(cond_obj.eval_condition(cond_field))
            if compound:
                result = Condition.get_condition_result(
                    results, conditional['type'])
            else:
                result = Condition.get_condition_result(results, cond_obj.type)
            if result:
                if compound and 'hidden' in conditional['state']:
                    field_hidden = conditional['state']['hidden']
                elif not compound and 'hidden' in cond_obj.state:
                    field_hidden = cond_obj.state['hidden']
                if compound and 'required' in conditional['state']:
                    field_required = conditional['state']['required']
                elif not compound and 'required' in cond_obj.state:
                    field_required = cond_obj.state['required']

        try:
            section_conditionals = section.conditionals
        except AttributeError:
            section_conditionals = []
        for conditional in section_conditionals:
            conditions, compound = Condition.check_condition(conditional)
            results = []
            for condition in conditions:
                condition_class = ConditionFactory.get_class(condition['type'])
                cond_obj = condition_class(condition)
                try:
                    cond_field = answers[cond_obj.field]
                except KeyError:
                    results.append(False)
                    continue
                results.append(cond_obj.eval_condition(cond_field))
            if compound:
                result = Condition.get_condition_result(
                    results, conditional['type'])
            else:
                result = Condition.get_condition_result(results, cond_obj.type)
            if result:
                if compound and 'hidden' in conditional['state']:
                    section_hidden = conditional['state']['hidden']
                elif not compound and 'hidden' in cond_obj.state:
                    section_hidden = cond_obj.state['hidden']

        try:
            page_conditionals = page.conditionals
        except AttributeError:
            page_conditionals = []
        for conditional in page_conditionals:
            conditions, compound = Condition.check_condition(conditional)
            results = []
            for condition in conditions:
                condition_class = ConditionFactory.get_class(condition['type'])
                cond_obj = condition_class(condition)
                try:
                    cond_field = answers[cond_obj.field]
                except KeyError:
                    results.append(False)
                    continue
                results.append(cond_obj.eval_condition(cond_field))
            if compound:
                result = Condition.get_condition_result(
                    results, conditional['type'])
            else:
                result = Condition.get_condition_result(results, cond_obj.type)
            if result:
                if compound and 'hidden' in conditional['state']:
                    field_hidden = conditional['state']['hidden']
                elif not compound and 'hidden' in cond_obj.state:
                    field_hidden = cond_obj.state['hidden']

        # It is considered hidden if either the field,
        # it's section or page are hidden
        return field_hidden or section_hidden or page_hidden, field_required

    def is_valid(self):
        """ Returns True if the form has no errors. Otherwise, False. """
        return not self.errors['errors']


class Section:

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)
        self.fields = {}


class Page:

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)
        self.sections = {}
