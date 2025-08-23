from django.db import models


class Ingredient(models.Model):
    """Модель для хранения данных об ингредиентах."""

    name = models.CharField(
        max_length=200,
        verbose_name="Название ингредиента",
        help_text="Введите название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=100,
        verbose_name="Единица измерения",
        help_text="Например, грамм, литр, шт.",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_constraint"
            ),
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"
