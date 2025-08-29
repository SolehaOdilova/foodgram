import io

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientNameSearch, RecipeQueryFilter
from api.mixins import RelationToggleMixin, SubscriptionManageMixin
from api.pagination import RecipePagination
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (FavoriteCreateSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeDetailSerializer, RecipeShortSerializer,
                             RelationStatusSerializer, SubscriptionSerializer,
                             TagSerializer, UserSerializer)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.shopping import build_shopping_list

User = get_user_model()


class RecipesViewSet(ModelViewSet, RelationToggleMixin):
    """
    ViewSet для работы с рецептами.
    Поддерживает избранное, корзину и скачивание списка покупок.
    """

    queryset = Recipe.objects.select_related("author")
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeQueryFilter
    pagination_class = RecipePagination
    toggle_serializer = RecipeShortSerializer

    def get_serializer_class(self):
        # эндпоинты связей
        if self.action in ["favorites", "cart"]:
            if self.request.method == "GET":
                return RelationStatusSerializer
            return FavoriteCreateSerializer

        if self.action in ["create", "partial_update"]:
            return RecipeCreateUpdateSerializer
        return RecipeDetailSerializer

    def get_queryset(self):
        user = self.request.user
        base = self.queryset.prefetch_related("tags")
        if user.is_authenticated:
            return (
                Recipe.objects.with_user_flags(user)
                .select_related("author")
                .prefetch_related("tags")
            )
        return base

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="favorite",
        permission_classes=[IsAuthenticated]
    )
    def favorites(self, request, pk=None):
        return self.toggle_relation(pk, Favorite)

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated])
    def cart(self, request, pk=None):
        return self.toggle_relation(pk, ShoppingCart)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_cart(self, request):
        shopping_list = build_shopping_list(request.user)
        file_buffer = io.BytesIO(shopping_list.encode("utf-8"))
        response = FileResponse(
            file_buffer,
            content_type="text/plain; charset=utf-8"
        )

        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        frontend_url = "http://localhost:3000"
        url = f"{frontend_url}/recipes/{recipe.id}/"
        return Response({"short-link": url})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тэгом."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получения списка ингредиентов.
    По умолчанию DRF ждёт ?search=...; если фронт шлёт ?name=...,
    подключи кастомный фильтр IngredientNameSearch в api/filters.py.
    """
    queryset = Ingredient.objects.order_by("name")
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientNameSearch]
    search_fields = ['^name']  # автокомплит с начала строки


class UserProfileViewSet(UserViewSet, SubscriptionManageMixin):
    """Вьюсет для профиля пользователя и подписок."""
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
        GET — проверить наличие подписки,
        POST — подписаться,
        DELETE — отписаться.
        """
        if request.method == "GET":
            user = request.user
            if user.is_anonymous:
                return Response({
                    "is_subscribed": False},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            is_subscribed = user.subscriptions.filter(author_id=id).exists()
            return Response(
                {"is_subscribed": is_subscribed},
                status=status.HTTP_200_OK
            )

        return self.add_and_delete(id)

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def my_subscriptions(self, request):
        """Список авторов, на которых подписан текущий пользователь."""
        user = request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        authors_qs = (
            User.objects
            .filter(subscribers__user=user)
            .annotate(recipes_count=Count("recipes_created"))
            .order_by("id")
        )
        page = self.paginate_queryset(authors_qs)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={"request": request}
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
