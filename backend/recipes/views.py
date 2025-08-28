import io

from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.pagination import RecipePagination

from .filters import RecipeQueryFilter
from .mixins import RelationToggleMixin
from .models import Recipe, Favorite, ShoppingCart, Ingredient, Tag
from .permissions import IsAuthorOrReadOnly
from .serializers import (RecipeCreateUpdateSerializer, RecipeDetailSerializer,
                          RecipeShortSerializer,
                          FavoriteCreateSerializer,
                          IngredientSerializer,
                          TagSerializer)
from .shopping import build_shopping_list
from recipes.permissions import IsAdminOrReadOnly
from rest_framework import viewsets, filters


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
        if self.action in ["create", "partial_update"]:
            return RecipeCreateUpdateSerializer
        elif self.action in ["favorite", "shopping_cart"]:  # POST / DELETE
            return FavoriteCreateSerializer
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
        url_path="favorite"
    )
    def favorites(self, request, pk=None):
        return self.toggle_relation(pk, Favorite)

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="shopping_cart"
    )
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

    Поддерживает фильтрацию по параметру `search`, который приходит с фронта.
    """

    serializer_class = IngredientSerializer
    pagination_class = None
    queryset = Ingredient.objects.order_by("name")
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']  # ищет с начала строки (как автокомплит)
