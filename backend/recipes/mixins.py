from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from .serializers import FavoriteSerializer


class RelationToggleMixin:
    """
    Миксин для добавления/удаления объекта
    через отдельные модели (Favorite, ShoppingCart).
    """

    def toggle_relation(self, obj_id, model_class):
        user = self.request.user
        obj = get_object_or_404(self.get_queryset(), id=obj_id)

        # Валидируем через сериализатор
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            data={}, context={"request": self.request, "obj_id": obj_id}
        )
        serializer.is_valid(raise_exception=True)

        if self.request.method in ("POST", "GET"):
            model_class.objects.get_or_create(user=user, recipe=obj)
            return Response(FavoriteSerializer(obj).data, status=201)

        if self.request.method == "DELETE":
            model_class.objects.filter(user=user, recipe=obj).delete()
            return Response(status=204)

        return Response(status=400)