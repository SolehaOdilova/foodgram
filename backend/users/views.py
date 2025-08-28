import base64

from django.core.files.base import ContentFile
from djoser.views import UserViewSet
from recipes.permissions import IsAuthorOrReadOnly
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.status import HTTP_401_UNAUTHORIZED
from users.mixins import SubscriptionManageMixin


from .pagination import RecipePagination
from .serializers import UserSerializer, SubscriptionSerializer


class UserProfileViewSet(UserViewSet, SubscriptionManageMixin):
    """
    Вьюсет для работы с профилем пользователя и его подписками.
    """

    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = RecipePagination
    add_serializer = SubscriptionSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="subscribe"
    )
    def toggle_subscription(self, request, id=None):
        """
        Проверить, добавить или,
        удалить подписку на другого пользователя.
        GET — проверить есть ли подписка,
        POST — подписаться,
        DELETE — отписаться.
        """
        if request.method == "GET":
            user = request.user
            if user.is_anonymous:
                return Response(
                    {"is_subscribed": False},
                    status=HTTP_401_UNAUTHORIZED
                )
            is_subscribed = user.subscriptions.filter(id=id).exists()
            return Response(
                {"is_subscribed": is_subscribed},
                status=status.HTTP_200_OK
            )

        return self.add_and_delete(id, "subscriptions")

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def my_subscriptions(self, request):
        """
        Получить список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)

        subscribed_authors = user.subscriptions.annotate(
            recipes_count=Count("recipes_created")
        )
        page = self.paginate_queryset(subscribed_authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["put", "patch"],
        url_path="me/avatar",
        permission_classes=[IsAuthorOrReadOnly],
    )
    def set_avatar(self, request):
        user = request.user
        serializer = UserSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
