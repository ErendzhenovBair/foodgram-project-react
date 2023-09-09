from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_superuser)


class RecipePermission(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in ['DELETE', 'PATCH', ]
                and request.user.is_user
                and request.user != obj.author
                or request.user.is_admin)
