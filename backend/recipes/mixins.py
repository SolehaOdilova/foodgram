from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from typing import Optional, Type
from rest_framework import serializers


class RelationToggleMixin:
    """
    Миксин для добавления/удаления объекта из связей M2M (например, избранное или корзина).
    """
    toggle_serializer: Optional[Type[serializers.Serializer]] = None

    def toggle_relation(self, obj_id, relation_field):
        user = self.request.user
        related_qs = getattr(user, relation_field)
        obj = get_object_or_404(self.get_queryset(), id=obj_id)

        is_attached = related_qs.filter(id=obj_id).exists()

        if self.request.method in ('POST', 'GET') and not is_attached:
            related_qs.add(obj)
            serializer = self.toggle_serializer(obj, context={'request': self.request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE' and is_attached:
            related_qs.remove(obj)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)
