from django.db import models

from .widgets.widgets import ColorWidget


class ColorField(models.CharField):
    description = "Hex color code"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 7
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['widget'] = ColorWidget
        return super().formfield(**kwargs)
