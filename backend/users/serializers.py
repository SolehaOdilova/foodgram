from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from .models import CustomUser
from recipes.models import Recipe


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор для получения информации о пользователе с полем подписки."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

    def validate_avatar(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Размер файла не должен превышать 5 МБ")
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Допустимы только файлы JPG и PNG")
        return value

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.subscriptions.filter(pk=obj.pk).exists()

    class Meta(DjoserUserSerializer.Meta):
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',  # добавили поле
        )


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для регистрации нового пользователя."""

    class Meta(DjoserUserCreateSerializer.Meta):
        model = CustomUser
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для данных пользователей, на которых подписан текущий пользователь, включая их рецепты."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        from recipes.serializers import RecipeShortSerializer
        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_subscribed', 'recipes', 'recipes_count'
        )