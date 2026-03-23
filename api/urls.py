from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandViewSet,
    ChangePasswordView,
    ClientViewSet,
    ClientAttachmentViewSet,
    ClientOwnerViewSet,
    LoginView,
    LogoutView,
    MeView,
    NegativeRemarkViewSet,
    NegativeRemarkOnTaskViewSet,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ScopeOfWorkViewSet,
    ServiceCategoryViewSet,
    TaskViewSet,
    TaskAttachmentViewSet,
    TypeOfWorkViewSet,
)

router = DefaultRouter()
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"service-categories", ServiceCategoryViewSet, basename="service-category")
router.register(r"type-of-work", TypeOfWorkViewSet, basename="type-of-work")
router.register(r"negative-remarks", NegativeRemarkViewSet, basename="negative-remark")
router.register(r"negative-remarks-on-task", NegativeRemarkOnTaskViewSet, basename="negative-remark-on-task")
router.register(r"task-attachments", TaskAttachmentViewSet, basename="task-attachment")
router.register(r"client-attachments", ClientAttachmentViewSet, basename="client-attachment")
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"client-owners", ClientOwnerViewSet, basename="client-owner")
router.register(r"scope-of-work", ScopeOfWorkViewSet, basename="scope-of-work")
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/password-reset/request/", PasswordResetRequestView.as_view(), name="auth-password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("", include(router.urls)),
]
