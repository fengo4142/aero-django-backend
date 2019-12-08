from django import forms
from airport.models import Airport
from django.contrib.gis.geos import Point


class AirportForm(forms.ModelForm):

    latitude = forms.FloatField(
        min_value=-90,
        max_value=90,
        required=True,
    )
    longitude = forms.FloatField(
        min_value=-180,
        max_value=180,
        required=True,
    )

    class Meta(object):
        model = Airport
        exclude = []
        widgets = {'location': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        coordinates = self.initial.get('location', None)
        if isinstance(coordinates, Point):
            self.initial['longitude'], self.initial['latitude'] = coordinates.tuple

    def clean(self):
        data = super().clean()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude and longitude:
            data['location'] = Point(longitude, latitude)
        return data
