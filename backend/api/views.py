import io

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientNameSearch, RecipeQueryFilter
from api.pagination import RecipePagination
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeDetailSerializer,
    SubscriptionSerializer,
    AddSubscriptionSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from recipes.shopping import build_shopping_list
from users.models import Subscription
from .serializers import (
    FavoriteAttachSerializer,
    CartAttachSerializer
)

User = get_user_model()


class RecipesViewSet(ModelViewSet):
    """
    ViewSet для работы с рецептами.
    Поддерживает избранное, корзину и скачивание списка покупок.
    """

    queryset = Recipe.objects.select_related("author")
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeQueryFilter
    pagination_class = RecipePagination

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

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="favorite",
        permission_classes=[IsAuthenticated]
    )
    def favorites(self, request, pk=None):
        if request.method == "POST":
            serializer = FavoriteAttachSerializer(
                data={},  # полей нет — создаём связь по context
                context={"request": request, "recipe_id": pk}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()
        if deleted == 0:
            return Response({"detail": "Рецепт не был в избранном."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post", "delete"], detail=True, url_path="shopping_cart",
            permission_classes=[IsAuthenticated])
    def cart(self, request, pk=None):
        if request.method == "POST":
            serializer = CartAttachSerializer(
                data={},
                context={"request": request, "recipe_id": pk}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()
        if deleted == 0:
            return Response({"detail": "Рецепт не был в корзине."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    """

    queryset = Ingredient.objects.order_by("name")
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientNameSearch]
    search_fields = ["^name"]  # автокомплит с начала строки


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """Профиль пользователя + подписки."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="subscribe",
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        target = get_object_or_404(User, pk=pk)

        if request.method == "POST":
            serializer = AddSubscriptionSerializer(
                data={}, context={"request": request, "target": target}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = SubscriptionSerializer(
                target,
                context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = Subscription.objects.filter(
            user=request.user, author=target
        ).delete()
        if deleted == 0:
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[IsAuthenticated]
    )
    def my_subscriptions(self, request):
        limit_raw = request.query_params.get("recipes_limit")
        try:
            limit = int(limit_raw) if limit_raw is not None else None
        except (TypeError, ValueError):
            limit = None

        recipes_qs = Recipe.objects.all()
        if limit and limit > 0:
            recipes_qs = recipes_qs[:limit]

        authors_qs = (
            User.objects
            .filter(subscribers__user=request.user)
            .annotate(recipes_count=Count("recipes_created"))
            .prefetch_related(Prefetch("recipes_created", queryset=recipes_qs))
        )

        page = self.paginate_queryset(authors_qs)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
