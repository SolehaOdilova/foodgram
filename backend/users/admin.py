from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "followers_count",
        "recipes_count",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("email",)
    readonly_fields = ("id",)
    empty_value_display = "---"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Добавляем аннотацию количества рецептов
        return qs.annotate(recipes_count=Count("recipes_created"))

    @admin.display(description="Подписчики")
    def followers_count(self, obj):
        return obj.subscribers.count()

    @admin.display(description="Рецепты")
    def recipes_count(self, obj):
        return getattr(obj, "recipes_count", 0)
