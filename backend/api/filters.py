from django_filters import rest_framework as django_filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class RecipeQueryFilter(django_filters.FilterSet):
    """Фильтры для рецептов: по автору, тэгам, избранному и корзине."""

    is_favorited = django_filters.BooleanFilter()
    is_in_shopping_cart = django_filters.BooleanFilter()
    author = django_filters.NumberFilter(field_name="author")
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name="tags__slug",
        to_field_name="slug",
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]


class IngredientNameSearch(SearchFilter):
    """Поиск ингредиентов по имени через параметр ?name=""."""

    search_param = "name"
