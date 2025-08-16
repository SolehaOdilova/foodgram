from django.contrib import admin
from .models import Recipe, RecipeIngredientAmount, RecipeTagRelation


class IngredientInline(admin.TabularInline):
    model = RecipeIngredientAmount
    extra = 1


class TagInline(admin.TabularInline):
    model = RecipeTagRelation
    extra = 1


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text', 'author')
    search_fields = ('name', 'author__username')
    inlines = [IngredientInline, TagInline]
