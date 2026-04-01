from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import CustomUser, Employee


class BaseImportExportAdmin(ImportExportModelAdmin, ModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, BaseImportExportAdmin):
    model = CustomUser
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
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


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, BaseImportExportAdmin):
    pass


@admin.register(Employee)
class EmployeeAdmin(BaseImportExportAdmin):
    list_display = ("id", "user", "designation", "salary", "created_at")
    list_display_links = ("id", "user")
    search_fields = ("user__email", "designation")
    ordering = ("user__email",)
