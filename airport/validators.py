import logging

from PIL import Image

from django.core.exceptions import ValidationError

from airport.utils import is_svg


def logo_validator(image):
    try:
        Image.open(image)
    except OSError:
        # File is not an image
        if not is_svg(image):
            raise ValidationError("Invlid file type for logo")
