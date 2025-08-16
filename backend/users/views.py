import base64
from django.core.files.base import ContentFile
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.status import HTTP_401_UNAUTHORIZED

from .pagination import RecipePagination
from .serializers import SubscriptionSerializer, CustomUserSerializer
from users.mixins import SubscriptionManageMixin
from recipes.permissions import IsAuthorOrReadOnly


class UserProfileViewSet(UserViewSet, SubscriptionManageMixin):
    """
    Вьюсет для работы с профилем пользователя и его подписками.
    """
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = RecipePagination
    add_serializer = SubscriptionSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @action(methods=['get', 'post', 'delete'], detail=True, url_path='subscribe')
    def toggle_subscription(self, request, id=None):
        """
        Проверить, добавить или удалить подписку на другого пользователя.
        GET — проверить есть ли подписка,
        POST — подписаться,
        DELETE — отписаться.
        """
        if request.method == 'GET':
            user = request.user
            if user.is_anonymous:
                return Response({'is_subscribed': False}, status=HTTP_401_UNAUTHORIZED)
            is_subscribed = user.subscriptions.filter(id=id).exists()
            return Response({'is_subscribed': is_subscribed}, status=status.HTTP_200_OK)

        return self.add_and_delete(id, 'subscriptions')

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def my_subscriptions(self, request):
        """
        Получить список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)

        subscribed_authors = user.subscriptions.all()
        page = self.paginate_queryset(subscribed_authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'patch'],
        url_path='me/avatar',
        permission_classes=[IsAuthorOrReadOnly]
    )
    def set_avatar(self, request):
        user = request.user
        avatar_file = request.data.get('avatar')

        if not avatar_file:
            return Response({"error": "Файл не передан"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(avatar_file, str) and avatar_file.startswith("data:image"):
            try:
                format, imgstr = avatar_file.split(";base64,")
                ext = format.split("/")[-1]
                avatar_file = ContentFile(base64.b64decode(imgstr), name=f"avatar.{ext}")
            except Exception:
                return Response({"error": "Некорректный формат base64"}, status=status.HTTP_400_BAD_REQUEST)

        valid_content_types = ['image/jpeg', 'image/png']
        if hasattr(avatar_file, 'content_type') and avatar_file.content_type not in valid_content_types:
            return Response({"error": "Только JPG или PNG"}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(avatar_file, 'size') and avatar_file.size > 5 * 1024 * 1024:
            return Response({"error": "Максимальный размер 5 МБ"}, status=status.HTTP_400_BAD_REQUEST)

        user.avatar = avatar_file
        user.save()

        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)