from typing import Optional, Type
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from django.conf import settings
from django.db import models


class SubscriptionManageMixin:
    """Миксин для управления подписками на пользователей."""

    add_serializer: Optional[Type[serializers.Serializer]] = None  # Будет установлен динамически

    def add_and_delete(self, user_id):
        user = self.request.user
        
        # Динамически импортируем модели
        User = models.get_model(settings.AUTH_USER_MODEL)
        Subscription = models.get_model('users', 'Subscription')
        
        target = get_object_or_404(User, id=user_id)

        # Динамически импортируем сериализатор
        from users.serializers import AddSubscriptionSerializer
        serializer = AddSubscriptionSerializer(
            context={"request": self.request, "target": target}
        )
        serializer.is_valid(raise_exception=True)

        if self.request.method == "POST":
            # Создаём подписку, если её ещё нет
            Subscription.objects.get_or_create(user=user, author=target)
            
            # Динамически импортируем UserSerializer
            from users.serializers import UserSerializer
            return Response(
                UserSerializer(target, context={"request": self.request}).data,
                status=status.HTTP_201_CREATED,
            )

        # DELETE: удаляем подписку
        deleted_count, _ = Subscription.objects.filter(
            user=user,
            author=target
        ).delete()
        if deleted_count == 0:
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
