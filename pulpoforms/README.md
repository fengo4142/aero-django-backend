
Pulpo Forms
===========

Pulpo Forms is a Python module that provides tools to create and validate forms from a schema inspired by the JSON schema. It includes support for field validation, and conditional logic to show fields, sections and pages.

***

Schema Description
------------------
The base schema is as follows:
```
    {
      "id": "FORM_ID",
      "version": 0,
      "fields": [],
      "sections": [],
      "pages": []
    }
```

The '`fields`' property
-----------------------
Each element of the ```fields``` property must follow one of the following field schemas. The available field types are:

#### `StringField`
```
    {
      "type": "string",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "conditionals": [],
      "validators: []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `contains`
* `minLength`
* `maxLength`

##### Available conditionals for this field type
* `empty`
* `equals`
* `startsWith`
* `endsWith`
* `contains`

#### `IntegerField`
```
    {
      "type": "integer",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minValue`
* `maxValue`

##### Available conditionals for this field type
* `empty`
* `equals`
* `greater`
* `greaterEqual`
* `lesserEqual`
* `lesser`

#### `BooleanField`
```
    {
      "type": "boolean",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* No validator available

##### Available conditionals for this field type
* `empty`
* `equals`

#### `SelectField`
```
    {
      "type": "select",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "values": [
        {
          "key": "value_key",
          "value": "Display value for this option"
        }
      ],
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* No validator available

##### Available conditionals for this field type
* `empty`
* `equals`

#### `MultiselectField`
```
    {
      "type": "multiselect",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "values": [
        {
          "key": "value_key",
          "value": "Display value for this option"
        }
      ],
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minLength`
* `maxLength`

##### Available conditionals for this field type
* `empty`
* `equals`
* `contains`

#### `EmailField`
```
    {
      "type": "email",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `contains`
* `minLength`
* `maxLength`

##### Available conditionals for this field type
* `empty`
* `equals`
* `contains`
* `startsWith`
* `endsWith`

#### `DateField`
```
    {
      "type": "date",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minValue`
* `maxValue`

##### Available conditionals for this field type
* `empty`
* `equals`
* `before`
* `after`

#### `DatetimeField`
```
    {
      "type": "datetime",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minValue`
* `maxValue`

##### Available conditionals for this field type
* `empty`
* `equals`
* `before`
* `after`

#### `DurationField`
```
    {
      "type": "duration",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minValue`
* `maxValue`

##### Available conditionals for this field type
* `empty`
* `equals`
* `greater`
* `greaterEqual`
* `lesserEqual`
* `lesser`

#### `TimeField`
```
    {
      "type": "time",
      "id": "field_id",
      "title": "Field text or form question",
      "tooltip": "Some help text for this field",
      "required": true,
      "hidden": false,
      "validators": [],
      "conditionals": []
    }
```
Where the `conditionals`, `validators`, `tooltip` and `hidden` properties are optional. If not present in the schema, the first two will be treated as empty lists, the third as an empty string and the last assumed `false`. All other properties are required.

##### Available validators for this field type
* `minValue`
* `maxValue`

##### Available conditionals for this field type
* `empty`
* `equals`
* `before`
* `after`

The '`sections`' property
-------------------------
```
    {
      "title": "Section title",
      "id": "section_id",
      "fields": [
        "field_1_id",
        "field_2_id",
        "field_3_id",
        "field_4_id"
      ],
      "conditionals": [],
      "hidden": false
    }
```
A *section* only needs an `id`, `title` and `fields` properties. The first two work the same way as in the fields. The `fields` property is a list of field ids that are included in the section. All fields must be included in one, and only one, section.
As with the fields, the `conditionals` and `hidden` properties are optional, and recieve the same treatment as in the previous case if they are not present.

The '`pages`' property
----------------------
```
    {
      "id": "page_id",
      "title": "Page title",
      "sections": [
        "section_1_id",
        "section_2_id",
        "section_3_id",
        "section_4_id"
      ],
      "conditionals": [],
      "hidden": false
    }
```
Same as `sections`. All sections must be included in one, and only one page.

The '`validators`' property
---------------------------
```
    {
      "type": "validator_type",
      "value": VALUE
    }
```

Available validator types are:
* `minLength`, with a value of type `integer`
* `maxLength`, with a value of type `integer`
* `contains`, with a value of type `string`
* `minValue`, with a value of type `integer`
* `maxValue`, with a value of type `integer`
* `maxSize`, with a value of type `integer`
* `fileTypes`, with a value of type `list` of `strings`

The '`conditionals`' property
-----------------------------
There are two types of conditional properties, simple and compound.

#### Simple conditions
```
  {
    "type": "condition_type",
    "field": "field_id",
    "value": "condition_value",
    "state": {
      "hidden": false
    }
  }
```
In simple conditions, the `type`, `field` and `state` properties are required. The `value` property is required for all condition types, except the `empty` condition.
`field` refers to the field who's value will be compared according to the defined condition.
The `state` property defines all the properties that will be applied to the field if the condition is satisfied.

The available condition types are:
* `empty`, which does not allow the `value` property,
* `equals`, with a value of type `string` or `integer`, depending of the type of field it references.
* `contains`, with a value of type `string`.
* `startsWith`, with a value of type `string`.
* `endsWith`, with a value of type `string`.
* `greater`, with a value of type `integer`.
* `greaterEqual`, with a value of type `integer`.
* `lesserEqual`, with a value of type `integer`.
* `lesser`, with a value of type `integer`.
* `before`, with a value of type `integer`.
* `after`, with a value of type `integer`.
* `maxDistanceTo`, with a value of type `integer`.
* `minDistanceTo`, with a value of type `integer`.

#### Compound conditions
```
  {
    "type": "compound_condition_type",
    "conditionList": [],
    "state": {
      "hidden": false
    }
  }
```
In this case, all properties are required.
Available types for compound conditions are `all` and `any`. Each element of `conditionList` property must be a simple condition *without* the `state` property, since the state belongs to the whole compound condition.