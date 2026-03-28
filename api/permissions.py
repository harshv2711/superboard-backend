from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Client
from users.models import CustomUser


def is_privileged_user(user):
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_superuser or user.role in {CustomUser.Role.SUPERUSER, CustomUser.Role.ADMIN})


def is_account_planner(user):
    return bool(user and user.is_authenticated and user.role == CustomUser.Role.ACCOUNT_PLANNER)


def is_art_director(user):
    return bool(user and user.is_authenticated and user.role == CustomUser.Role.ART_DIRECTOR)


def is_designer(user):
    return bool(user and user.is_authenticated and user.role == CustomUser.Role.DESIGNER)


def user_can_manage_client(user, client):
    if not user or not user.is_authenticated or client is None:
        return False
    if is_privileged_user(user):
        return True
    if not is_account_planner(user):
        return False
    return client.owners.filter(user_id=user.id).exists()


def user_can_fully_manage_task(user, task):
    client = get_client_for_object(task)
    if not user or not user.is_authenticated:
        return False
    if is_privileged_user(user):
        return True
    if is_art_director(user):
        return True
    return user_can_manage_client(user, client)


def user_can_designer_update_task(user, task):
    if not is_designer(user):
        return False
    return bool(task and getattr(task, "designer_id", None) == user.id)


def get_client_for_object(obj):
    if isinstance(obj, Client):
        return obj
    return getattr(obj, "client", None)


class IsClientOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return user_can_manage_client(request.user, get_client_for_object(obj))


class CanWriteTaskByRole(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return user_can_fully_manage_task(request.user, obj) or user_can_designer_update_task(request.user, obj)


class IsAuthenticatedAndCanManageNegativeRemarks(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_privileged_user(request.user) or is_art_director(request.user)
