import base64
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredientAmount,
    Tag,
    Favorite,
    ShoppingCart,
)
from users.models import User, Subscription


class Base64ImageField(serializers.ImageField):
    """Поле для приёма изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                fmt, imgstr = data.split(";base64,")
            except ValueError:
                raise serializers.ValidationError(
                    "Некорректный формат base64"
                )
            ext = fmt.split("/")[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"image.{ext}"
            )
        return super().to_internal_value(data)


class RelationStatusSerializer(serializers.Serializer):
    is_attached = serializers.BooleanField(read_only=True)


class IngredientAmountInputSerializer(serializers.ModelSerializer):
    """Для передачи ингредиентов при создании.
    редактировании рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient"
    )
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
        return (
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
    ingredients = IngredientInRecipeSerializer(
        source='recipeingredientamount_set',
        many=True,
        read_only=True
    )
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


class AuthorMiniSerializer(serializers.ModelSerializer):
    """Короткая карточка автора для вложенного использования."""
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = fields


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    author = AuthorMiniSerializer(read_only=True)
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
                    ingredient=ing["ingredient"],
                    amount=ing["amount"],
                )
                for ing in ingredients_data
            ]
        )

    def validate(self, attrs):
        tags = attrs.get("tags")
        ingredients = attrs.get("ingredients")

        # --- теги ---
        if tags is not None:
            if not tags:
                raise serializers.ValidationError(
                    {"tags": "Укажите хотя бы один тег."}
                )
            tag_ids = [t.id if hasattr(t, "id") else int(t) for t in tags]
            if len(tag_ids) != len(set(tag_ids)):
                raise serializers.ValidationError(
                    {"tags": "Теги не должны повторяться."}
                )

        # --- ингредиенты ---
        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError(
                    {"ingredients": "Необходимо указать ингредиенты."}
                )
            seen_ids = [ing["ingredient"].id for ing in ingredients]
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
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        instance.tags.set(tags)
        instance.ingredients.clear()
        self._save_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeDetailSerializer(
            instance,
            context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Карточка рецепта для избранного/корзины."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class BaseAttachSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для связей (избранное / корзина).
    Ничего не валидируем «вручную» — полагаемся на уникальный
    констрейнт в БД. Возвращаем карточку рецепта.
    """

    class Meta:
        # модель задаётся в наследниках через Meta.model
        fields = ()  # записываем через context/URL, явных входных полей нет
        read_only_fields = ()

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        recipe_id = self.context.get("recipe_id")
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        model = self.Meta.model
        try:
            obj = model.objects.create(user=user, recipe=recipe)
        except IntegrityError:
            raise serializers.ValidationError({"detail": "Уже добавлено."})
        return obj


class FavoriteAttachSerializer(BaseAttachSerializer):
    class Meta(BaseAttachSerializer.Meta):
        model = Favorite


class CartAttachSerializer(BaseAttachSerializer):
    class Meta(BaseAttachSerializer.Meta):
        model = ShoppingCart


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = "__all__"


# ----- Пользователи / Подписки -----


class SubscriptionSerializer(UserSerializer):
    """Пользователь, на которого подписан текущий.
    плюс список его рецептов.
    """

    recipes = RecipeShortSerializer(
        source="recipes_created",
        many=True,
        read_only=True,
    )
    recipes_count = serializers.IntegerField(read_only=True)

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

    class Meta:
        model = Subscription
        fields = ()

    def validate(self, attrs):
        request = self.context["request"]
        target = self.context["target"]
        if target == request.user:
            raise serializers.ValidationError(
                "Нельзя подписаться на себя."
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        target = self.context["target"]
        try:
            return Subscription.objects.create(
                user=request.user, author=target
            )
        except IntegrityError:
            # уже подписан
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
