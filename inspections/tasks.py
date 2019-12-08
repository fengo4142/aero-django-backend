import logging
from django.conf import settings
from celery import shared_task
from inspections.models import (
    InspectionTemplateForm, InspectionTemplateVersion,
    AirportTemplatesRelation
)
from airport.models import Airport
import requests

logger = logging.getLogger('backend')


def update_templates(templates):
    """
    Update templates
    """
    for t in templates:
        form = InspectionTemplateForm.objects.filter(repo_id=t['repo_id'])
        if form.exists():
            if (form.first().versions.latest('number').number < t['number']):
                form = form.first()
            else:
                form = None
        else:
            form = InspectionTemplateForm.objects.create(
                title=t['title'], repo_id=t['repo_id']
            )
            for airport in Airport.objects.all():
                relation = AirportTemplatesRelation()
                relation.airport = airport
                relation.form = form
                relation.selected_version = t['number']
                relation.save()

        if form is not None:
            form.title = t['title']
            version = InspectionTemplateVersion()
            version.title = t['title']
            # version.icon = t['icon']
            version.schema = t['schema']
            version.additionalInfo = t['additionalInfo']
            version.form = form
            version.save()
    return


@shared_task(name='fetch_templates')
def fetch_templates():
    """
    Fetches templates
    """

    templates = {}
    try:
        r = requests.get(
            "{}/api/templates".format(settings.CENTRAL_REPO_URL),
            headers={"Authorization": "Api-Key {}".format(
                settings.CENTRAL_REPO_API_KEY)}
        )
        templates = r.json()
    except Exception:
        return
    update_templates(templates)
    return
