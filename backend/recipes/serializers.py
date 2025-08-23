import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from ingredients.models import Ingredient
from rest_framework import exceptions, serializers
from tags.models import Tag
from tags.serializers import TagSerializer
from users.serializers import CustomUserSerializer

from .models import Recipe, RecipeIngredientAmount


class Base64ImageField(serializers.ImageField):
    """Обработка изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"temp.{ext}")
        return super().to_internal_value(data)


class IngredientAmountInputSerializer(serializers.ModelSerializer):
    """Для передачи ингредиентов при создании/редактировании рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[MinValueValidator(
            1,
            message="Минимум 1 единица ингредиента"
        )]
    )

    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сокращённый вывод рецепта (для избранного, корзины и т.д.)."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Для отображения ингредиента внутри рецепта."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = ("id", "name", "amount", "measurement_unit")

    def get_amount(self, obj):
        return f"{obj.amount} {obj.ingredient.measurement_unit}"


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор рецепта для отображения."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredientAmount.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountInputSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                1,
                message="Время готовки должно быть минимум 1 минута"
            )
        ]
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredientAmount.objects.bulk_create(
            [
                RecipeIngredientAmount(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(pk=ingredient["id"]),
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients_data
            ]
        )

    def validate_tags(self, tags):
        if not tags:
            raise exceptions.ValidationError("Укажите хотя бы один тег.")
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise exceptions.ValidationError("Необходимо указать ингредиенты.")
        seen_ids = [ing["id"] for ing in ingredients]
        if len(set(seen_ids)) != len(seen_ids):
            raise exceptions.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return ingredients

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)

        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            self._save_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeDetailSerializer(instance, context=self.context).data
