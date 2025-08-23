from rest_framework import viewsets

from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получения списка ингредиентов.
    Поддерживает фильтрацию по параметру `name`, который приходит с фронта.
    """

    serializer_class = IngredientSerializer
    pagination_class = None
    queryset = Ingredient.objects.all()

    def get_queryset(self):
        queryset = Ingredient.objects.order_by("name")
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
