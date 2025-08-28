from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from recipes.models import Recipe
from rest_framework import serializers
from recipes.fields import Base64ImageField
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для получения информации.
    о пользователе с полем подписки.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    def validate_avatar(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
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
            and request.user.subscriptions.filter(pk=obj.pk).exists()
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
            "avatar",  # добавили поле
        )


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для регистрации нового пользователя."""

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


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для данных пользователей.
    на которых подписан текущий пользователь, включая их рецепты.
    """

    recipes = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = None
        if request:
            try:
                limit = int(request.GET.get("recipes_limit", 0))
            except (ValueError, TypeError):
                limit = 0

        recipes = Recipe.objects.filter(author=obj)
        if limit and limit > 0:
            recipes = recipes[:limit]

        from recipes.serializers import RecipeShortSerializer
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

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
        request = self.context['request']
        target_user = self.context['target']

        if target_user == request.user:
            raise serializers.ValidationError("Нельзя подписаться на себя.")

        if request.method == "POST" and target_user in request.user.subscriptions.all():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )

        if request.method == "DELETE" and target_user not in request.user.subscriptions.all():
            raise serializers.ValidationError(
                "Вы не подписаны на этого пользователя."
            )

        return attrs
