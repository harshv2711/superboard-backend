from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
import re
from rest_framework import serializers
from .models import (
    Brand,
    Client,
    ClientAttachment,
    ClientMonthlyAmount,
    ClientOwner,
    Group,
    GroupMember,
    NegativeRemark,
    NegativeRemarkOnTask,
    ScopeOfWork,
    ServiceCategory,
    Task,
    TaskAttachment,
    TaskOnStage,
    TaskStage,
    TypeOfWork,
)

User = get_user_model()


class ClientSerializer(serializers.ModelSerializer):
    clientInterface = serializers.CharField(source="client_interface")
    clientInterfaceContactNumber = serializers.CharField(source="client_interface_contact_number", required=False, allow_blank=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    accentColor = serializers.CharField(source="accent_color", required=False, allow_blank=True)
    owner_user_ids = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "clientInterface",
            "clientInterfaceContactNumber",
            "logo",
            "accentColor",
            "owner_user_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Client name cannot be empty.")
        return cleaned

    def get_owner_user_ids(self, obj):
        return list(obj.owners.values_list("user_id", flat=True))

    def validate_accent_color(self, value):
        cleaned = value.strip()
        if not cleaned:
            return ""
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", cleaned):
            raise serializers.ValidationError("Accent color must be a valid hex color like #1F6FEB.")
        return cleaned.upper()


class ClientAttachmentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = ClientAttachment
        fields = [
            "id",
            "client",
            "client_name",
            "file",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "client_name", "file_url", "created_at", "updated_at"]


class ClientMonthlyAmountSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = ClientMonthlyAmount
        fields = [
            "id",
            "client",
            "client_name",
            "date",
            "amt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "client_name", "created_at", "updated_at"]

    def validate_amt(self, value):
        if value is None:
            raise serializers.ValidationError("Amount is required.")
        return value


class ScopeOfWorkSerializer(serializers.ModelSerializer):
    service_category_name = serializers.CharField(source="service_category.name", read_only=True)
    totalUnit = serializers.IntegerField(source="total_unit", required=False, min_value=0)
    type_of_work = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TypeOfWork.objects.all(),
        required=False,
    )
    type_of_work_names = serializers.SerializerMethodField()

    class Meta:
        model = ScopeOfWork
        fields = [
            "id",
            "client",
            "service_category",
            "service_category_name",
            "type_of_work",
            "type_of_work_names",
            "deliverable_name",
            "description",
            "total_unit",
            "totalUnit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        for field_name in ["deliverable_name", "description"]:
            value = attrs.get(field_name)
            if value is not None:
                attrs[field_name] = str(value).strip()

        total_unit = attrs.get("total_unit")
        if total_unit is not None and total_unit < 0:
            raise serializers.ValidationError({"total_unit": "Must be zero or greater."})

        client = attrs.get("client", getattr(self.instance, "client", None))
        service_category = attrs.get("service_category", getattr(self.instance, "service_category", None))
        if client and service_category:
            duplicate_scope_qs = ScopeOfWork.objects.filter(client=client, service_category=service_category)
            if self.instance is not None:
                duplicate_scope_qs = duplicate_scope_qs.exclude(pk=self.instance.pk)
            if duplicate_scope_qs.exists():
                raise serializers.ValidationError(
                    {"service_category": "This client already has a scope of work for the selected service category."}
                )

        type_of_work_items = attrs.get("type_of_work")
        if type_of_work_items is not None:
            attrs["type_of_work"] = list(type_of_work_items)
        return attrs

    def get_type_of_work_names(self, obj):
        return list(obj.type_of_work.values_list("work_type_name", flat=True))


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Brand name cannot be empty.")

        qs = Brand.objects.filter(name__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Brand with this name already exists.")

        return cleaned


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Group name cannot be empty.")

        qs = Group.objects.filter(name__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Group with this name already exists.")

        return cleaned


class GroupMemberSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = GroupMember
        fields = ["id", "group", "group_name", "user", "user_email", "created_at"]
        read_only_fields = ["id", "group_name", "user_email", "created_at"]

    def validate(self, attrs):
        group = attrs.get("group") or getattr(self.instance, "group", None)
        user = attrs.get("user") or getattr(self.instance, "user", None)

        if group and user:
            qs = GroupMember.objects.filter(group=group, user=user)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("This user is already a member of the selected group.")

        return attrs


class TypeOfWorkSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TypeOfWork
        fields = [
            "id",
            "work_type_name",
            "point",
            "redo_point",
            "major_changes_point",
            "minor_changes_point",
            "task_count",
        ]

    def validate_work_type_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Work type name cannot be empty.")

        qs = TypeOfWork.objects.filter(work_type_name__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Type of work with this name already exists.")

        return cleaned

    def get_task_count(self, obj):
        return obj.tasks.count()


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "description"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Service category name cannot be empty.")

        qs = ServiceCategory.objects.filter(name__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Service category with this name already exists.")

        return cleaned

    def validate_description(self, value):
        return value.strip()


class NegativeRemarkSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = NegativeRemark
        fields = ["id", "remark_name", "description", "point", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_remark_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Remark name cannot be empty.")
        return cleaned

    def validate_description(self, value):
        return value.strip()

    def get_task_count(self, obj):
        return obj.task_links.count()


class NegativeRemarkOnTaskSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.task_name", read_only=True)
    negative_remark_name = serializers.CharField(source="negative_remark.remark_name", read_only=True)
    negative_remark_description = serializers.CharField(source="negative_remark.description", read_only=True)
    point = serializers.DecimalField(source="negative_remark.point", max_digits=12, decimal_places=4, read_only=True)

    class Meta:
        model = NegativeRemarkOnTask
        fields = [
            "id",
            "task",
            "task_name",
            "negative_remark",
            "negative_remark_name",
            "negative_remark_description",
            "point",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "task_name",
            "negative_remark_name",
            "negative_remark_description",
            "point",
            "created_at",
            "updated_at",
        ]


class TaskAttachmentSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.task_name", read_only=True)
    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = TaskAttachment
        fields = [
            "id",
            "task",
            "task_name",
            "file",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "task_name", "file_url", "created_at", "updated_at"]


class TaskStageSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskStage
        fields = ["id", "name", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "task_count", "created_at", "updated_at"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Task stage name cannot be empty.")

        qs = TaskStage.objects.filter(name__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Task stage with this name already exists.")

        return cleaned

    def get_task_count(self, obj):
        return obj.task_links.count()


class TaskOnStageSerializer(serializers.ModelSerializer):
    task_stage_name = serializers.CharField(source="task_stage.name", read_only=True)
    task_name = serializers.CharField(source="task.task_name", read_only=True)
    client_name = serializers.CharField(source="task.client.name", read_only=True)
    designer_name = serializers.CharField(source="task.designer.email", read_only=True)
    type_of_work_name = serializers.CharField(source="task.type_of_work.work_type_name", read_only=True)
    target_date = serializers.DateField(source="task.target_date", read_only=True)
    priority = serializers.CharField(source="task.priority", read_only=True)

    class Meta:
        model = TaskOnStage
        fields = [
            "id",
            "task_stage",
            "task_stage_name",
            "task",
            "task_name",
            "client_name",
            "designer_name",
            "type_of_work_name",
            "target_date",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "task_stage_name",
            "task_name",
            "client_name",
            "designer_name",
            "type_of_work_name",
            "target_date",
            "priority",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        task = attrs.get("task") or getattr(self.instance, "task", None)
        if not task:
            return attrs

        qs = TaskOnStage.objects.filter(task=task)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"task": "This task is already assigned to a stage."})

        return attrs


class DesignerKpiSummarySerializer(serializers.Serializer):
    designer_id = serializers.IntegerField()
    month = serializers.CharField()
    total_kpi_score = serializers.FloatField()


class ClientOwnerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = ClientOwner
        fields = ["id", "user", "user_email", "client", "client_name", "created_at"]
        read_only_fields = ["id", "user_email", "client_name", "created_at"]

    def validate(self, attrs):
        user = attrs.get("user") or getattr(self.instance, "user", None)
        client = attrs.get("client") or getattr(self.instance, "client", None)

        if user and user.role != User.Role.ACCOUNT_PLANNER:
            raise serializers.ValidationError({"user": "Client owner must be an account planner."})

        if user and client:
            qs = ClientOwner.objects.filter(user=user, client=client)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("This client is already assigned to this user.")

        return attrs


class TaskSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    scope_of_work_name = serializers.CharField(source="scope_of_work.deliverable_name", read_only=True)
    designer_name = serializers.CharField(source="designer.email", read_only=True)
    type_of_work_name = serializers.CharField(source="type_of_work.work_type_name", read_only=True)
    service_category_name = serializers.CharField(source="scope_of_work.service_category.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.email", read_only=True)
    revision_of_task_name = serializers.CharField(source="revision_of.task_name", read_only=True)
    redo_of_task_name = serializers.CharField(source="redo_of.task_name", read_only=True)
    revisions_count = serializers.IntegerField(source="revisions.count", read_only=True)
    redos_count = serializers.IntegerField(source="redos.count", read_only=True)
    redo_of_task_id = serializers.SerializerMethodField()
    isRevision = serializers.SerializerMethodField()
    isRedo = serializers.SerializerMethodField()
    is_marked_completed_by_superadmin = serializers.SerializerMethodField()
    is_marked_completed_by_account_planner = serializers.SerializerMethodField()
    is_marked_completed_by_art_director = serializers.SerializerMethodField()
    is_marked_completed_by_designer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "client",
            "client_name",
            "scope_of_work",
            "scope_of_work_name",
            "revision_of",
            "redo_of",
            "revision_of_task_name",
            "redo_of_task_name",
            "redo_of_task_id",
            "revision_no",
            "redo_no",
            "revision_count",
            "redo_count",
            "task_name",
            "instructions",
            "InstructionsByArtDirector",
            "revision_type",
            "priority",
            "stage",
            "designer",
            "designer_name",
            "type_of_work",
            "type_of_work_name",
            "service_category_name",
            "created_by",
            "created_by_name",
            "target_date",
            "slides",
            "impressions",
            "ctr",
            "engagement_rate",
            "promotion_type",
            "is_marked_completed_by_superadmin",
            "is_marked_completed_by_account_planner",
            "is_marked_completed_by_art_director",
            "is_marked_completed_by_designer",
            "have_major_changes",
            "have_minor_changes",
            "isRevision",
            "isRedo",
            "excellence",
            "excellence_reason",
            "revisions_count",
            "redos_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["revision_no", "redo_no", "revision_count", "redo_count", "created_by", "created_at", "updated_at"]

    def validate_slides(self, value):
        if value < 1:
            raise serializers.ValidationError("Slides must be at least 1.")
        return value

    def validate_ctr(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("CTR cannot be negative.")
        return value

    def validate_engagement_rate(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Engagement rate cannot be negative.")
        return value

    def validate(self, attrs):
        """
        If revision_of is set, client can be omitted and will be auto-filled in model.save().
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        task_name = attrs.get("task_name")
        if isinstance(task_name, str):
            attrs["task_name"] = task_name.strip()

        revision_of = attrs.get("revision_of", getattr(self.instance, "revision_of", None))
        redo_of = attrs.get("redo_of", getattr(self.instance, "redo_of", None))
        scope_of_work = attrs.get("scope_of_work", getattr(self.instance, "scope_of_work", None))
        client = attrs.get("client", getattr(self.instance, "client", None))
        effective_task_name = attrs.get("task_name", getattr(self.instance, "task_name", ""))
        if scope_of_work and client and scope_of_work.client_id != client.id:
            raise serializers.ValidationError(
                {"scope_of_work": "Selected scope of work must belong to the same client as the task."}
            )

        if self.instance is None and not revision_of and not redo_of and not scope_of_work:
            raise serializers.ValidationError({"scope_of_work": "Scope of work is required."})

        if self.instance is None and not revision_of and not redo_of and not str(effective_task_name or "").strip():
            raise serializers.ValidationError({"task_name": "Task name is required."})

        effective_have_major_changes = attrs.get(
            "have_major_changes",
            getattr(self.instance, "have_major_changes", False),
        )
        effective_have_minor_changes = attrs.get(
            "have_minor_changes",
            getattr(self.instance, "have_minor_changes", False),
        )
        current_stage = Task.normalize_stage(getattr(self.instance, "stage", Task.Stage.BACKLOG))
        current_completion_state = Task.completion_state_for_stage(current_stage)
        effective_stage = self._resolve_effective_stage(attrs)
        effective_completion_state = Task.completion_state_for_stage(effective_stage)

        current_account_planner_completed = current_completion_state["is_marked_completed_by_account_planner"]
        current_art_director_completed = current_completion_state["is_marked_completed_by_art_director"]
        current_designer_completed = current_completion_state["is_marked_completed_by_designer"]
        effective_account_planner_completed = effective_completion_state["is_marked_completed_by_account_planner"]
        effective_art_director_completed = effective_completion_state["is_marked_completed_by_art_director"]
        effective_designer_completed = effective_completion_state["is_marked_completed_by_designer"]

        legacy_completion_keys = {
            "is_marked_completed_by_superadmin",
            "is_marked_completed_by_account_planner",
            "is_marked_completed_by_art_director",
            "is_marked_completed_by_designer",
        }
        stage_change_requested = "stage" in attrs or any(key in self.initial_data for key in legacy_completion_keys)

        if self.instance is not None and stage_change_requested and user and user.is_authenticated and not user.is_superuser:
            workflow_order = [
                Task.Stage.BACKLOG,
                Task.Stage.ON_GOING,
                Task.Stage.COMPLETE,
                Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                Task.Stage.APPROVED,
            ]
            next_stage = effective_stage

            if current_stage != next_stage:
                allowed_stage_scopes = {
                    User.Role.DESIGNER: {
                        Task.Stage.BACKLOG,
                        Task.Stage.ON_GOING,
                        Task.Stage.COMPLETE,
                    },
                    User.Role.ART_DIRECTOR: {
                        Task.Stage.COMPLETE,
                        Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                    },
                    User.Role.ACCOUNT_PLANNER: {
                        Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                        Task.Stage.APPROVED,
                    },
                }

                allowed_stages = allowed_stage_scopes.get(user.role)
                if allowed_stages is not None:
                    if current_stage not in allowed_stages or next_stage not in allowed_stages:
                        raise serializers.ValidationError(
                            {
                                "stage": "You can only move tasks within the stages allowed for your role."
                            }
                        )

                    current_index = workflow_order.index(current_stage)
                    next_index = workflow_order.index(next_stage)
                    if next_index > current_index and (next_index - current_index) != 1:
                        raise serializers.ValidationError(
                            {
                                "stage": "You can only move tasks one step forward within your workflow."
                            }
                        )

        if revision_of and not effective_have_major_changes and not effective_have_minor_changes:
            raise serializers.ValidationError(
                {
                    "have_major_changes": "Revision changes are required for revision tasks.",
                    "have_minor_changes": "Revision changes are required for revision tasks.",
                }
            )

        if self.instance is not None and user and user.is_authenticated and user.role == User.Role.ACCOUNT_PLANNER:
            forbidden_fields = {
                "is_marked_completed_by_superadmin": "Account planners cannot edit the superadmin completion flag.",
                "is_marked_completed_by_art_director": "Account planners cannot edit the art director completion flag.",
                "is_marked_completed_by_designer": "Account planners cannot edit the designer completion flag.",
            }
            errors = {
                field_name: message
                for field_name, message in forbidden_fields.items()
                if field_name in self.initial_data
            }
            if errors:
                raise serializers.ValidationError(errors)
            if (
                effective_account_planner_completed
                and (not effective_art_director_completed or not effective_designer_completed)
            ):
                raise serializers.ValidationError(
                    {
                        "is_marked_completed_by_account_planner": (
                            "Account planners can mark a task completed only after the art director and designer have completed it."
                        )
                    }
                )
        if user and user.is_authenticated and user.role == User.Role.ART_DIRECTOR:
            forbidden_fields = {
                "is_marked_completed_by_superadmin": "Art directors cannot edit the superadmin completion flag.",
                "is_marked_completed_by_account_planner": "Art directors cannot edit the account planner completion flag.",
                "is_marked_completed_by_designer": "Art directors cannot edit the designer completion flag.",
            }
            errors = {
                field_name: message
                for field_name, message in forbidden_fields.items()
                if field_name in self.initial_data
            }
            if errors:
                raise serializers.ValidationError(errors)
            if (
                current_account_planner_completed
                and "is_marked_completed_by_art_director" in self.initial_data
                and effective_art_director_completed != current_art_director_completed
            ):
                raise serializers.ValidationError(
                    {
                        "is_marked_completed_by_art_director": (
                            "Art directors cannot modify their completion status after the account planner has completed the task."
                        )
                    }
                )
            if effective_art_director_completed and not effective_designer_completed:
                raise serializers.ValidationError(
                    {
                        "is_marked_completed_by_art_director": (
                            "Art directors can mark a task completed only after the designer has completed it."
                        )
                    }
                )
        if user and user.is_authenticated and not user.is_superuser and user.role == User.Role.DESIGNER:
            allowed_fields = {"is_marked_completed_by_designer", "stage"}
            forbidden_fields = {
                field_name: "Designers can only update their own completion flag or stage."
                for field_name in self.initial_data
                if field_name not in allowed_fields
            }
            if forbidden_fields:
                raise serializers.ValidationError(forbidden_fields)
            if effective_designer_completed != current_designer_completed:
                if current_art_director_completed:
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the art director has completed the task."
                            )
                        }
                    )
                if current_account_planner_completed:
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the account planner has completed the task."
                            )
                        }
                    )
                if current_completion_state["is_marked_completed_by_superadmin"]:
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the superadmin has completed the task."
                            )
                        }
                    )

        attrs["stage"] = effective_stage
        return attrs

    def get_isRevision(self, obj):
        return bool(obj.revision_of_id)

    def get_isRedo(self, obj):
        return bool(obj.redo_of_id)

    def get_redo_of_task_id(self, obj):
        return obj.redo_of_id

    def get_is_marked_completed_by_superadmin(self, obj):
        return Task.completion_state_for_stage(obj.stage)["is_marked_completed_by_superadmin"]

    def get_is_marked_completed_by_account_planner(self, obj):
        return Task.completion_state_for_stage(obj.stage)["is_marked_completed_by_account_planner"]

    def get_is_marked_completed_by_art_director(self, obj):
        return Task.completion_state_for_stage(obj.stage)["is_marked_completed_by_art_director"]

    def get_is_marked_completed_by_designer(self, obj):
        return Task.completion_state_for_stage(obj.stage)["is_marked_completed_by_designer"]

    def _resolve_effective_stage(self, attrs):
        raw_stage = attrs.get("stage", getattr(self.instance, "stage", Task.Stage.BACKLOG))
        stage = Task.normalize_stage(raw_stage)

        legacy_completion_keys = [
            "is_marked_completed_by_superadmin",
            "is_marked_completed_by_account_planner",
            "is_marked_completed_by_art_director",
            "is_marked_completed_by_designer",
        ]
        if not any(key in self.initial_data for key in legacy_completion_keys):
            return stage

        def as_bool(key):
            value = self.initial_data.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)

        if as_bool("is_marked_completed_by_superadmin") or as_bool("is_marked_completed_by_account_planner"):
            return Task.Stage.APPROVED
        if as_bool("is_marked_completed_by_art_director"):
            return Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL
        if as_bool("is_marked_completed_by_designer"):
            return Task.Stage.COMPLETE
        if "is_marked_completed_by_designer" in self.initial_data:
            return Task.Stage.ON_GOING if stage != Task.Stage.BACKLOG else Task.Stage.BACKLOG
        if "is_marked_completed_by_art_director" in self.initial_data:
            return Task.Stage.COMPLETE
        if "is_marked_completed_by_account_planner" in self.initial_data:
            return Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL
        return stage


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return email

    def validate_password(self, value):
        try:
            validate_password(value)
        except django_exceptions.ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return {"sent": True}

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return {"sent": True, "uid": uid, "token": token}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except django_exceptions.ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError({"uid": "Invalid reset uid."}) from exc

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "role"]

    def validate_email(self, value):
        email = value.strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("User with this email already exists.")
        return email

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context.get("user"))
        except django_exceptions.ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        user = self.context["user"]
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
