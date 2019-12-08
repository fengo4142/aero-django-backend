import logging

logger = logging.getLogger('backend')


def build_schema(airport_changes, template):
    """
      this functions makes the merge between the airport
      hanges and the template.
      The result of this is the schema.
    """
    # ------------------------------------------------------------------------------
    # IF THERE IS A TEMPLATE ASOCIATED WE MERGE THE TEMPLATE FIELDS
    # WITH THE INSPECTION CHANGES
    schema = template.schema
    sections = schema["sections"]
    fields = schema["fields"]
    template_detail_fields = [
        f for f in fields if f['id'] in sections[0]['fields']
    ]
    template_checklist_fields = [
        f for f in fields if f['id'] in sections[1]['fields']
    ]

    # ------------------------------------------------------------------------------
    # MERGE AIRPORT CHANGES IN FIELDS WITH TEMPLATES

    airport_fields = []
    changedFields = [f for f in airport_changes['fields'] if 'hidden' not in f]

    for f in changedFields:
        if f['id'] in sections[0]['fields']:
            item = [fi for fi in template_detail_fields if fi['id'] == f['id']][0]
            item['order'] = f['order']
            airport_fields.append(item)
        else:
            airport_fields.append(f)

    # ------------------------------------------------------------------
    # IF THERE AREN'T CHANGES IN THE SCHEMA, WE MUST RETURN
    # THE TEMPLATE FIELDS
    if len(airport_changes['fields']) > 0:
        detail_fields = sorted(
            airport_fields, key=lambda x: x['order']
        )
    else:
        detail_fields = template_detail_fields

    # ------------------------------------------------------------------
    # MERGE AIRPORT CHANGES IN CHECKLIST WITH TEMPLATES

    airport_checklist = []
    changedChecklist = [f for f in airport_changes['inspectionChecklist'] if 'hidden' not in f]

    for f in changedChecklist:
        if f['id'] in sections[1]['fields']:
            item = [
                fi for fi in template_checklist_fields
                if fi['id'] == f['id']
            ][0]
            item['order'] = f['order']
            airport_checklist.append(item)
        else:
            airport_checklist.append(f)

    # ------------------------------------------------------------------
    # IF THERE AREN'T CHANGES IN THE SCHEMA, WE MUST RETURN
    # THE TEMPLATE FIELDS
    if len(airport_changes['inspectionChecklist']) > 0:
        checklist_fields = sorted(
            airport_checklist, key=lambda x: x['order']
        )
    else:
        checklist_fields = template_checklist_fields

    allFields = detail_fields + checklist_fields

    # ONCE ORDERED, WE DONT NEED THE ORDER PROPERTY ANYMORE
    list(map(lambda x: x.pop('order', None), allFields))
    schema['fields'] = allFields

    schema["sections"][0]['fields'] = [f['id'] for f in detail_fields]
    schema["sections"][1]['fields'] = [f['id'] for f in checklist_fields]

    logger.info("****************************************************")
    logger.info(schema)
    logger.info("****************************************************")
    return schema
