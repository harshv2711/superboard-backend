from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomUser, Employee


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_per_page = 25
    ordering = ("-date_joined",)
    list_display = ("id", "email", "role", "first_name", "last_name", "is_staff", "is_active")
    list_display_links = ("id", "email")
    search_fields = ("email", "first_name", "last_name", "role")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "designation", "salary", "created_at")
    list_display_links = ("id", "user")
    search_fields = ("user__email", "designation")
    ordering = ("user__email",)
