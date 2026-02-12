from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, RecipeIngredientAmount, Tag


class IngredientInline(admin.TabularInline):
    model = RecipeIngredientAmount
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "text", "author", "favorites_count")
    search_fields = ("name", "author__username")
    inlines = [IngredientInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(favorited_count=Count("favorited"))

    @admin.display(description="В избранном", ordering="favorited_count")
    def favorites_count(self, obj):
        return obj.favorited_count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)  # фильтр по единице измерения
    ordering = ("name",)  # сортировка по названию
    readonly_fields = ("id",)  # поле id только для чтения

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "measurement_unit"),
                "description": "Управление ингредиентами",
            },
        ),
    )
