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
from .models import Recipe
from .permissions import IsAuthorOrReadOnly
from .serializers import (RecipeCreateUpdateSerializer, RecipeDetailSerializer,
                          RecipeShortSerializer)
from .shopping import build_shopping_list


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

    def create(self, request, *args, **kwargs):
        """
        Создаёт рецепт и возвращает полную информацию о нём
        с использованием RecipeDetailSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        recipe = serializer.instance
        full_data = RecipeDetailSerializer(
            recipe, context=self.get_serializer_context()
        )
        return Response(full_data.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="favorite"
    )
    def favorites(self, request, pk=None):
        return self.toggle_relation(pk, "favorited_recipes")

    @action(
        methods=["get", "post", "delete"],
        detail=True,
        url_path="shopping_cart"
    )
    def cart(self, request, pk=None):
        return self.toggle_relation(pk, "shopping_cart_recipes")

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
