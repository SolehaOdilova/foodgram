from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Разрешает только чтение всем пользователям,
    а изменение — только администраторам.
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and getattr(request.user, "is_admin", False)
        )


class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешает редактирование объекта только его автору.
    Остальные могут только просматривать.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
