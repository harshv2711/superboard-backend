from django.contrib import admin
from django.contrib.auth import get_user_model
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import DateWidget, ForeignKeyWidget

from .models import Brand, Client, ClientAttachment, ClientOwner, NegativeRemark, NegativeRemarkOnTask, ScopeOfWork, ServiceCategory, Task, TaskAttachment, TypeOfWork

User = get_user_model()


class BrandResource(resources.ModelResource):
    class Meta:
        model = Brand
        fields = ("id", "name")
        export_order = ("id", "name")
        import_id_fields = ("id",)


class TaskResource(resources.ModelResource):
    client = fields.Field(
        column_name="client",
        attribute="client",
        widget=ForeignKeyWidget(Client, "name"),
    )
    designer = fields.Field(
        column_name="designer",
        attribute="designer",
        widget=ForeignKeyWidget(User, "email"),
    )
    created_by = fields.Field(
        column_name="created_by",
        attribute="created_by",
        widget=ForeignKeyWidget(User, "email"),
    )
    type_of_work = fields.Field(
        column_name="type_of_work",
        attribute="type_of_work",
        widget=ForeignKeyWidget(TypeOfWork, "work_type_name"),
    )
    scope_of_work = fields.Field(
        column_name="scope_of_work",
        attribute="scope_of_work",
        widget=ForeignKeyWidget(ScopeOfWork, "id"),
    )
    revision_of = fields.Field(
        column_name="revision_of",
        attribute="revision_of",
        widget=ForeignKeyWidget(Task, "id"),
    )
    redo_of = fields.Field(
        column_name="redo_of",
        attribute="redo_of",
        widget=ForeignKeyWidget(Task, "id"),
    )
    target_date = fields.Field(
        column_name="target_date",
        attribute="target_date",
        widget=DateWidget(format="%Y-%m-%d"),
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "client",
            "task_name",
            "instructions",
            "InstructionsByArtDirector",
            "priority",
            "designer",
            "created_by",
            "type_of_work",
            "scope_of_work",
            "target_date",
            "is_marked_completed_by_superadmin",
            "is_marked_completed_by_account_planner",
            "is_marked_completed_by_art_director",
            "is_marked_completed_by_designer",
            "revision_of",
            "redo_of",
            "revision_no",
            "redo_no",
            "revision_count",
            "redo_count",
            "excellence",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ("id",)
        skip_unchanged = True
        report_skipped = True


@admin.register(Brand)
class BrandAdmin(ImportExportModelAdmin):
    resource_class = BrandResource

    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(TypeOfWork)
class TypeOfWorkAdmin(admin.ModelAdmin):
    list_display = ("id", "work_type_name", "point")
    search_fields = ("work_type_name",)
    ordering = ("work_type_name",)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(NegativeRemark)
class NegativeRemarkAdmin(admin.ModelAdmin):
    list_display = ("id", "remark_name", "point", "created_at")
    search_fields = ("remark_name", "description")
    ordering = ("-created_at", "-id")


@admin.register(NegativeRemarkOnTask)
class NegativeRemarkOnTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "negative_remark", "created_at")
    search_fields = ("task__task_name", "task__client__name", "negative_remark__remark_name")
    list_filter = ("task__client", "negative_remark")
    ordering = ("-created_at", "-id")
    autocomplete_fields = ("task", "negative_remark")


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "file", "created_at")
    search_fields = ("task__task_name", "task__client__name", "file")
    list_filter = ("task__client", "created_at")
    ordering = ("-created_at", "-id")
    autocomplete_fields = ("task",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "logo",
        "accent_color",
        "client_interface",
        "client_interface_contact_number",
        "created_at",
    )
    search_fields = ("name", "client_interface", "client_interface_contact_number")
    ordering = ("name",)


@admin.register(ClientAttachment)
class ClientAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "file", "created_at")
    search_fields = ("client__name", "file")
    list_filter = ("client", "created_at")
    ordering = ("-created_at", "-id")
    autocomplete_fields = ("client",)


@admin.register(ClientOwner)
class ClientOwnerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "client", "created_at")
    search_fields = ("user__email", "client__name")
    list_filter = ("user", "client")
    ordering = ("user__email", "client__name")
    autocomplete_fields = ("user", "client")


@admin.register(ScopeOfWork)
class ScopeOfWorkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "service_category_display",
        "deliverable_name",
        "unit",
    )
    search_fields = ("client__name", "deliverable_name", "description")
    list_filter = ("client", "service_category")
    ordering = ("client", "service_category__name", "deliverable_name")
    autocomplete_fields = ("client", "service_category")
    filter_horizontal = ("type_of_work",)

    @admin.display(ordering="total_unit", description="Total Unit")
    def unit(self, obj):
        return obj.total_unit


@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    resource_class = TaskResource

    list_display = (
        "id",
        "client",
        "scope_of_work",
        "task_name",
        "task_kind",
        "priority",
        "designer",
        "created_by",
        "type_of_work",
        "target_date",
        "excellence",
        "revision_of",
        "redo_of",
    )
    list_filter = ("client", "scope_of_work", "priority", "designer", "created_by", "target_date")
    search_fields = ("id", "task_name", "instructions", "client__name", "scope_of_work__deliverable_name", "designer__email", "created_by__email")
    ordering = ("-target_date", "-created_at")
    autocomplete_fields = ("client", "scope_of_work", "designer", "created_by", "type_of_work", "revision_of", "redo_of")

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Core", {"fields": ("id", "client", "scope_of_work", "priority", "designer", "created_by", "type_of_work")}),
        ("Task Details", {"fields": ("task_name", "instructions", "InstructionsByArtDirector")}),
        ("Timeline", {"fields": ("target_date",)}),
        ("Revision", {"fields": ("revision_of", "revision_no", "revision_count")}),
        ("Redo", {"fields": ("redo_of", "redo_no", "redo_count")}),
        (
            "Completion",
            {
                "fields": (
                    "is_marked_completed_by_superadmin",
                    "is_marked_completed_by_account_planner",
                    "is_marked_completed_by_art_director",
                    "is_marked_completed_by_designer",
                )
            },
        ),
        ("Scoring", {"fields": ("excellence",)}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Task Type")
    def task_kind(self, obj):
        if obj.redo_of_id:
            return "Redo"
        if obj.revision_of_id:
            return "Revision"
        return "Original"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("client", "scope_of_work", "designer", "created_by", "type_of_work", "revision_of", "redo_of")
