from django.db import models


class Tag(models.Model):
    """Модель для работы с тэгом."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        unique=True,
    )
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет',
        unique=True,
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='slug',
        unique=True,
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name
