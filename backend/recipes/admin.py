from django.contrib import admin

from .models import Recipe, RecipeIngredientAmount, Tag, Ingredient


class IngredientInline(admin.TabularInline):
    model = RecipeIngredientAmount
    extra = 1


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "text", "author")
    search_fields = ("name", "author__username")
    inlines = [IngredientInline]


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
