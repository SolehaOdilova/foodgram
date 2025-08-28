# api/mixins.py
from typing import Optional, Type

from django.apps import apps
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.response import Response


class RelationToggleMixin:
    """
    Общая логика для эндпоинтов Favorite / ShoppingCart.
    Валидация — в сериализаторе. Импорты сериализаторов ленивые.
    """

    def toggle_relation(self, obj_id: int, model_class):
        # ленивые импорты, чтобы не было циклических зависимостей
        from api.serializers import (
            RelationStatusSerializer,
            FavoriteCreateSerializer,
            RecipeShortSerializer,
        )

        user = self.request.user
        recipe = get_object_or_404(self.get_queryset(), id=obj_id)

        if self.request.method == "GET":
            attached = model_class.objects.filter(user=user, recipe=recipe).exists()
            data = RelationStatusSerializer({"is_attached": attached}).data
            return Response(data, status=status.HTTP_200_OK)

        # POST / DELETE — валидируем правила
        validator = FavoriteCreateSerializer(
            data={},
            context={
                "request": self.request,
                "obj_id": obj_id,
                "recipe_qs": self.get_queryset(),
            },
        )
        validator.is_valid(raise_exception=True)

        if self.request.method == "POST":
            model_class.objects.get_or_create(user=user, recipe=recipe)
            data = RecipeShortSerializer(recipe, context={"request": self.request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        model_class.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionManageMixin:
    """Подписка/отписка на пользователей (users.Subscription)."""

    # Можно переопределить во ViewSet, чтобы вернуть другой сериализатор пользователя
    add_serializer: Optional[Type[serializers.Serializer]] = None

    def add_and_delete(self, user_id: int) -> Response:
        # ленивые импорты, чтобы избежать циклов
        from api.serializers import AddSubscriptionSerializer, UserSerializer

        user = self.request.user

        # Получаем модели без прямых импортов
        app_label, model_name = settings.AUTH_USER_MODEL.split(".")
        User = apps.get_model(app_label, model_name)
        Subscription = apps.get_model("users", "Subscription")

        target = get_object_or_404(User, id=user_id)

        # Валидация бизнес-правил — в сериализаторе
        validator = AddSubscriptionSerializer(
            data={}, context={"request": self.request, "target": target}
        )
        validator.is_valid(raise_exception=True)

        if self.request.method == "POST":
            Subscription.objects.get_or_create(user=user, author=target)
            serializer_cls = self.add_serializer or UserSerializer
            data = serializer_cls(target, context={"request": self.request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = Subscription.objects.filter(user=user, author=target).delete()
        if deleted == 0:
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

