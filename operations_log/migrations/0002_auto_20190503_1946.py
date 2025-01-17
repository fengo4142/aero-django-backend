# Generated by Django 2.1.3 on 2019-05-03 19:46

from django.db import migrations


def create_default_form_for_airports(apps, schema_editor):
    Airport = apps.get_model('airport', 'Airport')
    LogForm = apps.get_model('operations_log', 'LogForm')
    LogVersion = apps.get_model('operations_log', 'LogVersion')

    for airport in Airport.objects.all():
        log_form = LogForm.objects.create(
            airport=airport,
            title="{} Operations log form".format(airport.code)
        )
        LogVersion.objects.create(form=log_form, status=1)


class Migration(migrations.Migration):

    dependencies = [
        ('operations_log', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_default_form_for_airports,
            migrations.RunPython.noop),
        migrations.RunPython(
            migrations.RunPython.noop),
    ]
