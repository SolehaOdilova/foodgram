from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
    UserProfileViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register(r"recipes", RecipesViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"users", UserProfileViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
]
