from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from rest_framework import exceptions, serializers

from .models import Recipe, RecipeIngredientAmount, Tag, Ingredient
from .fields import Base64ImageField


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

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = ("id", "name", "amount", "measurement_unit")


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тэгами."""

    class Meta:
        model = Tag
        fields = "__all__"


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор рецепта для отображения."""

    author = serializers.SerializerMethodField(read_only=True)
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

    author = serializers.SerializerMethodField(read_only=True)
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
                    ingredient_id=ingredient["id"],
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients_data
            ]
        )

    def validate(self, attrs):
        tags = attrs.get("tags")
        ingredients = attrs.get("ingredients")

        # Проверка тегов
        if tags is not None:
            if not tags:
                raise exceptions.ValidationError({
                    "tags": "Укажите хотя бы один тег."
                })

        # Проверка ингредиентов
        if ingredients is not None:
            if not ingredients:
                raise exceptions.ValidationError({
                    "ingredients": "Необходимо указать ингредиенты."
                })

            seen_ids = [ing["id"] for ing in ingredients]
            if len(set(seen_ids)) != len(seen_ids):
                raise exceptions.ValidationError({
                    "ingredients": "Ингредиенты не должны повторяться."
                })

        return attrs

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


class FavoriteSerializer(serializers.ModelSerializer):
    """Для вывода информации о рецепте в избранном/корзине."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteCreateSerializer(serializers.Serializer):
    """Валидация при добавлении или удалении рецепта из избранного."""

    def validate(self, attrs):
        user = self.context['request'].user
        obj_id = self.context.get('obj_id')
        if not obj_id:
            raise serializers.ValidationError(
                "Не указан объект для добавления/удаления."
            )

        is_attached = user.favorites.filter(id=obj_id).exists()

        if self.context['request'].method == 'POST' and is_attached:
            raise serializers.ValidationError("Рецепт уже в избранном.")
        if self.context['request'].method == 'DELETE' and not is_attached:
            raise serializers.ValidationError("Рецепт не в избранном.")

        return attrs


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = "__all__"
