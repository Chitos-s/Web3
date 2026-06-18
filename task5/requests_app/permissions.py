from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import RoleChoices, get_user_role


class RequestAccessPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user)
        if request.method in SAFE_METHODS:
            return role in {RoleChoices.MODERATOR, RoleChoices.ADMIN} or obj.owner_id == request.user.id
        return obj.editable_by(request.user)


class ModeratorOrAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in {RoleChoices.MODERATOR, RoleChoices.ADMIN}


class ChangeHistoryPermission(BasePermission):
    """Позволяет просматривать историю заявки владельцу и модераторам/админам."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user)
        if role in {RoleChoices.MODERATOR, RoleChoices.ADMIN}:
            return True
        return obj.request.owner_id == request.user.id
