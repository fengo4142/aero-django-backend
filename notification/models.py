from django.db import models

class Section(models.Model):
    section = models.CharField(max_length=255)
    class Meta:
        verbose_name = "Secttion"
        verbose_name_plural = "Sections"
