from django.db import models
from django.contrib.postgres.fields import JSONField
from forms.utils import STATUS, DRAFT, PUBLISHED, EXPIRED
from datetime import datetime
from django.utils import timezone
from django import forms


class PasswordField(forms.CharField):
    widget = forms.PasswordInput

class PasswordModelField(models.CharField):

    def formfield(self, **kwargs):
        defaults = {'form_class': PasswordField}
        defaults.update(kwargs)
        return super(PasswordModelField, self).formfield(**defaults)

class Form(models.Model):
    """
    Forms of the app.
    """
    title = models.CharField(max_length=100)
    # removed onwer until we have cognito integration
    # owner = models.ForeignKey('auth.User', related_name='forms', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title',)
        abstract = True


def version_default():
    return {
        "id": "", "version": 1, "fields": [], "sections": [], "pages": []
    }


# # method for updating
# @receiver(post_save, sender=Form, dispatch_uid="create_default_version")
# def create_default_version(sender, instance, created, **kwargs):
#     if created:
#         version = Version()
#         version.form = instance
#         version.save()


class Version(models.Model):
    number = models.IntegerField(default=1)
    schema = JSONField(default=version_default, blank=True)
    status = models.IntegerField(choices=STATUS, default=DRAFT)
    publish_date = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "Form: '{title}' - Version: {version}".format(
            title=self.form.__str__(), version=str(self.number))

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.number = self.form.versions.count() + 1

        if ((self.status == PUBLISHED) and
                (self.publish_date is None or self.publish_date == '')):
            self.publish_date = timezone.now()
            # If there are previous published version,
            # its status is changed to expired.
            prev_versions = self.form.versions.filter(status=PUBLISHED)
            if len(prev_versions) > 0:
                for prev in prev_versions:
                    prev.status = EXPIRED
                    prev.expiry_date = datetime.now()
                    prev.save()
        super(Version, self).save(*args, **kwargs)


class Answer(models.Model):
    date = models.DateTimeField(auto_now=True)
    response = JSONField(default=dict)

    class Meta:
        abstract = True


def template_default():
    return {
        "id": "", "version": 1, "fields": [],
        "sections": [{"title": "", "fields": [], "id":"1"}],
        "pages": [{"sections": ["1"], "title":"", "id":"1"}]
    }


# class FormTemplate(models.Model):
#     title = models.CharField(max_length=100)
#     schema = JSONField(default=template_default, blank=True)

#     def __str__(self):
#         return "Section: '{title}'".format(title=self.title)
