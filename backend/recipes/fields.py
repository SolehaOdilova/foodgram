# recipes/fields.py
import base64
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Обработка изображений в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                format, imgstr = data.split(";base64,")
            except ValueError:
                raise serializers.ValidationError("Некорректный формат base64")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"avatar.{ext}")
        return super().to_internal_value(data)
