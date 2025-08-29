from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

MAX_LENGTH = 200
MAX_RECIPE_NAME_LENGTH = 100


class RecipeQuerySet(models.QuerySet):
    """Дополнительные методы для аннотаций избранного и корзины."""

    def with_user_flags(self, user):
        return self.annotate(
            is_favorited=Exists(
                user.favorited_recipes.filter(id=OuterRef("id"))
            ),
            is_in_shopping_cart=Exists(
                user.shopping_cart_recipes.filter(id=OuterRef("id"))
            ),
        )


class Tag(models.Model):
    """Модель для работы с тэгом."""

    name = models.CharField(
        verbose_name="Название",
        max_length=MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name="slug",
        max_length=MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для хранения данных об ингредиентах."""

    name = models.CharField(
        verbose_name="Название ингредиента",
        help_text="Введите название ингредиента",
        max_length=MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        help_text="Например, грамм, литр, шт.",
        max_length=MAX_RECIPE_NAME_LENGTH,
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


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes_created",
        verbose_name="Автор рецепта",
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        max_length=MAX_LENGTH,
    )
    image = models.ImageField(
        upload_to="recipe_images/",
        verbose_name="Изображение рецепта",
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredientAmount",
        related_name="recipes_with_ingredient",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes_with_tag",
        verbose_name="Теги",
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время готовки (минуты)",
    )

    objects = RecipeQuerySet.as_manager()

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранные рецепты пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.recipe}"


class ShoppingCart(models.Model):
    """Список покупок пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.recipe}"


class RecipeIngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient} – {self.amount} для {self.recipe}"
