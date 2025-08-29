from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredientAmount, Tag
from users.models import User


class RelationStatusSerializer(serializers.Serializer):
    is_attached = serializers.BooleanField(read_only=True)


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
    """Сокращённый вывод рецепта (для избранного, корзины и т.п.)."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Для отображения ингредиента внутри рецепта."""
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient",
        queryset=Ingredient.objects.all(),
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


class UserSerializer(DjoserUserSerializer):
    """Пользователь с признаком подписки и аватаром."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    def validate_avatar(self, value):
        if value:
            if getattr(value, "size", 0) > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Размер файла не должен превышать 5 МБ"
                )
            if not value.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise serializers.ValidationError(
                    "Допустимы только файлы JPG и PNG"
                )
        return value

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and not request.user.is_anonymous
            and request.user.subscriptions.filter(author=obj).exists()
        )

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Регистрация нового пользователя."""
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password"
        )


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
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
            "id", "tags", "author", "ingredients",
            "is_favorited", "is_in_shopping_cart",
            "name", "image", "text", "cooking_time",
        )

    def get_ingredients(self, obj):
        qs = RecipeIngredientAmount.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(qs, many=True).data


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
        validators=[MinValueValidator(
            1,
            message="Время готовки должно быть минимум 1 минута"
        )]
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

    def get_author(self, obj):
        u = self.context["request"].user
        return {
            "id": u.id,
            "username": getattr(u, "username", ""),
            "email": getattr(u, "email", ""),
        }

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredientAmount.objects.bulk_create(
            [
                RecipeIngredientAmount(
                    recipe=recipe,
                    ingredient_id=ing["id"],
                    amount=ing["amount"],
                )
                for ing in ingredients_data
            ]
        )

    def validate(self, attrs):
        tags = attrs.get("tags")
        ingredients = attrs.get("ingredients")

        if tags is not None and not tags:
            raise serializers.ValidationError(
                {"tags": "Укажите хотя бы один тег."}
            )

        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError(
                    {"ingredients": "Необходимо указать ингредиенты."}
                )

            seen_ids = [ing["id"] for ing in ingredients]
            if len(seen_ids) != len(set(seen_ids)):
                raise serializers.ValidationError(
                    {"ingredients": "Ингредиенты не должны повторяться."}
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context["request"].user,
            **validated_data,
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
    """Карточка рецепта для избранного/корзины."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteCreateSerializer(serializers.Serializer):
    """Валидация при добавлении/удалении рецепта из избранного."""
    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        obj_id = self.context.get("obj_id")
        if not obj_id:
            raise serializers.ValidationError(
                "Не указан объект для добавления/удаления."
            )

        is_attached = user.favorites.filter(recipe_id=obj_id).exists()

        if request.method == "POST" and is_attached:
            raise serializers.ValidationError("Рецепт уже в избранном.")
        if request.method == "DELETE" and not is_attached:
            raise serializers.ValidationError("Рецепт не в избранном.")

        return attrs


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = "__all__"


# ----- Пользователи / Подписки -----

class SubscriptionSerializer(UserSerializer):
    """Пользователь, на которого подписан текущий, плюс список его рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = None
        if request:
            try:
                limit = int(request.GET.get("recipes_limit", 0))
            except (ValueError, TypeError):
                limit = 0

        qs = Recipe.objects.filter(author=obj).order_by("id")
        if limit and limit > 0:
            qs = qs[:limit]
        return RecipeShortSerializer(qs, many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )


class AddSubscriptionSerializer(serializers.Serializer):
    """Валидация при подписке/отписке от пользователя."""
    def validate(self, attrs):
        request = self.context["request"]
        target_user = self.context["target"]

        if target_user == request.user:
            raise serializers.ValidationError("Нельзя подписаться на себя.")

        qs = request.user.subscriptions.filter(author=target_user)

        if request.method == "POST" and qs.exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        if request.method == "DELETE" and not qs.exists():
            raise serializers.ValidationError(
                "Вы не подписаны на этого пользователя."
            )

        return attrs
