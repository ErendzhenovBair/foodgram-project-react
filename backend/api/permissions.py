from rest_framework.permissions import SAFE_METHODS, BasePermission

CANNOT_UPDATE_OTHER_CONTENT = 'It is not allowed to change content!'


class IsAuthorOrReadOnly(BasePermission):

    message = CANNOT_UPDATE_OTHER_CONTENT

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user
                or obj.author.is_admin)
