from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets

from .serializers import UserSerializer

User = get_user_model()


class IsAuthenticatedOrCreate(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action == "create":
            return True
        return bool(request.user and request.user.is_authenticated)


class IsSelfOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.pk == request.user.pk


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related("employee_profile").order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrCreate, IsSelfOrStaff]
    search_fields = ["email", "role", "first_name", "last_name"]
    ordering_fields = ["id", "email", "role", "date_joined"]
    ordering = ["-date_joined"]
