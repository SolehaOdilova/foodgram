from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from recipes.views import RecipesViewSet, TagViewSet, IngredientViewSet
from users.views import UserProfileViewSet

router = DefaultRouter()
router.register("users", UserProfileViewSet, basename="users")
router.register("recipes", RecipesViewSet, basename="recipes")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/", include(router.urls)),
    # Djoser auth
    path("api/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.authtoken")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
