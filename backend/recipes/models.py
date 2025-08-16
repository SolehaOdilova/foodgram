from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

from ingredients.models import Ingredient
from tags.models import Tag
from users.models import CustomUser


class RecipeQuerySet(models.QuerySet):
    """Дополнительные методы для аннотаций избранного и корзины."""

    def with_user_flags(self, user):
        return self.annotate(
            is_favorited=Exists(
                user.favorited_recipes.filter(
                    id=OuterRef('id')
                )
            ),
            is_in_shopping_cart=Exists(
                user.shopping_cart_recipes.filter(
                    id=OuterRef('id')
                )
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes_created',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipe_images/',
        verbose_name='Изображение рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        'ingredients.Ingredient',
        through='RecipeIngredientAmount',
        related_name='recipes_with_ingredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        'tags.Tag',
        through='RecipeTagRelation',
        related_name='recipes_with_tag',
        verbose_name='Теги',
    )
    favorited_by = models.ManyToManyField(
        CustomUser,
        related_name='favorited_recipes',
        blank=True,
        verbose_name='Добавлено в избранное',
    )
    in_shopping_carts_of = models.ManyToManyField(
        CustomUser,
        related_name='shopping_cart_recipes',
        blank=True,
        verbose_name='В списках покупок',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время готовки (минуты)',
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name  # исправлено с title на name


class RecipeIngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'ingredients.Ingredient',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'


class RecipeTagRelation(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        'tags.Tag',
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'