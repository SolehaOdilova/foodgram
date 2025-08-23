from typing import Optional, Type

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from users.models import CustomUser


class SubscriptionManageMixin:
    """Миксин для управления подписками на пользователей."""

    serializer_class = None  # Определяется во ViewSet
    add_serializer: Optional[Type[serializers.Serializer]] = None

    def add_and_delete(self, id, relation_name):
        user = self.request.user
        try:
            id = int(id)
            target = get_object_or_404(CustomUser, id=id)
            relation = getattr(user, relation_name)

            if self.request.method == "POST":
                if relation.filter(id=id).exists():
                    return Response(
                        {"errors": "Вы уже подписаны на этого пользователя."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                relation.add(target)
                serializer = self.add_serializer(
                    target, context={"request": self.request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            if self.request.method == "DELETE":
                if not relation.filter(id=id).exists():
                    return Response(
                        {"errors": "Вы не подписаны на этого пользователя."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                relation.remove(target)
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"errors": "Метод не поддерживается."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        except Exception as e:
            return Response(
                {"errors": f"Внутренняя ошибка: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
