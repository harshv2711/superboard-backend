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
    ClientOwner,
    NegativeRemark,
    NegativeRemarkOnTask,
    ScopeOfWork,
    ServiceCategory,
    Task,
    TaskAttachment,
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


class TypeOfWorkSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TypeOfWork
        fields = ["id", "work_type_name", "point", "task_count"]

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
    class Meta:
        model = NegativeRemark
        fields = ["id", "remark_name", "description", "point", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_remark_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Remark name cannot be empty.")
        return cleaned

    def validate_description(self, value):
        return value.strip()


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
            "priority",
            "designer",
            "designer_name",
            "type_of_work",
            "type_of_work_name",
            "service_category_name",
            "created_by",
            "created_by_name",
            "target_date",
            "is_marked_completed_by_superadmin",
            "is_marked_completed_by_account_planner",
            "is_marked_completed_by_art_director",
            "is_marked_completed_by_designer",
            "isRevision",
            "isRedo",
            "excellence",
            "revisions_count",
            "redos_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["revision_no", "redo_no", "revision_count", "redo_count", "created_by", "created_at", "updated_at"]

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

        if not revision_of and not redo_of and not str(effective_task_name or "").strip():
            raise serializers.ValidationError({"task_name": "Task name is required."})

        if self.instance is not None and user and user.is_authenticated and user.role == User.Role.ACCOUNT_PLANNER:
            forbidden_fields = {
                "is_marked_completed_by_superadmin": "Account planners cannot edit the superadmin completion flag.",
                "is_marked_completed_by_art_director": "Account planners cannot edit the art director completion flag.",
                "is_marked_completed_by_designer": "Account planners cannot edit the designer completion flag.",
            }
            errors = {
                field_name: message
                for field_name, message in forbidden_fields.items()
                if field_name in attrs
            }
            if errors:
                raise serializers.ValidationError(errors)
            effective_account_planner_completed = attrs.get(
                "is_marked_completed_by_account_planner",
                getattr(self.instance, "is_marked_completed_by_account_planner", False),
            )
            effective_art_director_completed = attrs.get(
                "is_marked_completed_by_art_director",
                getattr(self.instance, "is_marked_completed_by_art_director", False),
            )
            effective_designer_completed = attrs.get(
                "is_marked_completed_by_designer",
                getattr(self.instance, "is_marked_completed_by_designer", False),
            )
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
                if field_name in attrs
            }
            if errors:
                raise serializers.ValidationError(errors)
            current_account_planner_completed = getattr(self.instance, "is_marked_completed_by_account_planner", False)
            current_art_director_completed = getattr(self.instance, "is_marked_completed_by_art_director", False)
            effective_art_director_completed = attrs.get(
                "is_marked_completed_by_art_director",
                current_art_director_completed,
            )
            effective_designer_completed = attrs.get(
                "is_marked_completed_by_designer",
                getattr(self.instance, "is_marked_completed_by_designer", False),
            )
            if (
                current_account_planner_completed
                and "is_marked_completed_by_art_director" in attrs
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
            allowed_fields = {"is_marked_completed_by_designer"}
            forbidden_fields = {
                field_name: "Designers can only update their own completion flag."
                for field_name in attrs
                if field_name not in allowed_fields
            }
            if forbidden_fields:
                raise serializers.ValidationError(forbidden_fields)
            current_designer_completed = getattr(self.instance, "is_marked_completed_by_designer", False)
            next_designer_completed = attrs.get("is_marked_completed_by_designer", current_designer_completed)
            if "is_marked_completed_by_designer" in attrs and next_designer_completed != current_designer_completed:
                if getattr(self.instance, "is_marked_completed_by_art_director", False):
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the art director has completed the task."
                            )
                        }
                    )
                if getattr(self.instance, "is_marked_completed_by_account_planner", False):
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the account planner has completed the task."
                            )
                        }
                    )
                if getattr(self.instance, "is_marked_completed_by_superadmin", False):
                    raise serializers.ValidationError(
                        {
                            "is_marked_completed_by_designer": (
                                "Designers cannot modify their completion status after the superadmin has completed the task."
                            )
                        }
                    )
        return attrs

    def get_isRevision(self, obj):
        return bool(obj.revision_of_id)

    def get_isRedo(self, obj):
        return bool(obj.redo_of_id)

    def get_redo_of_task_id(self, obj):
        return obj.redo_of_id


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
