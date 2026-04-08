from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Employee

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    designation = serializers.CharField(source="employee_profile.designation", required=False, allow_blank=True)
    salary = serializers.DecimalField(source="employee_profile.salary", max_digits=12, decimal_places=2, required=False, allow_null=True)
    has_employee_profile = serializers.SerializerMethodField()
    remove_employee_profile = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "first_name",
            "last_name",
            "designation",
            "salary",
            "has_employee_profile",
            "remove_employee_profile",
            "password",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate_email(self, value):
        email = value.strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("User with this email already exists.")
        return email

    def validate_role(self, value):
        request = self.context.get("request")
        if value in {User.Role.SUPERUSER, User.Role.ADMIN}:
            if not request or not request.user or not request.user.is_staff:
                raise serializers.ValidationError("Only staff users can assign admin or superuser role.")
        return value

    def validate_is_staff(self, value):
        request = self.context.get("request")
        if value and (not request or not request.user or not request.user.is_staff):
            raise serializers.ValidationError("Only staff users can grant staff access.")
        return value

    def validate_is_superuser(self, value):
        request = self.context.get("request")
        if value and (not request or not request.user or not request.user.is_superuser):
            raise serializers.ValidationError("Only superusers can grant superuser access.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        employee_profile_data = validated_data.pop("employee_profile", None)
        validated_data.pop("remove_employee_profile", None)

        user = User.objects.create_user(password=password, **validated_data)
        if employee_profile_data:
            self._upsert_employee_profile(user, employee_profile_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        employee_profile_data = validated_data.pop("employee_profile", None)
        remove_employee_profile = validated_data.pop("remove_employee_profile", False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        if remove_employee_profile and hasattr(instance, "employee_profile"):
            instance.employee_profile.delete()
        elif employee_profile_data is not None:
            self._upsert_employee_profile(instance, employee_profile_data)

        return instance

    def get_has_employee_profile(self, obj):
        return hasattr(obj, "employee_profile")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        employee_profile_data = attrs.get("employee_profile")
        remove_employee_profile = attrs.get("remove_employee_profile", False)
        role = attrs.get("role", getattr(self.instance, "role", User.Role.DESIGNER))
        is_superuser = attrs.get("is_superuser", getattr(self.instance, "is_superuser", False))

        if is_superuser:
            attrs["is_staff"] = True
            if "role" not in attrs:
                attrs["role"] = User.Role.SUPERUSER
            elif role != User.Role.SUPERUSER:
                raise serializers.ValidationError({"role": "Users with superuser status must use the superuser role."})

        if attrs.get("role", role) == User.Role.SUPERUSER and not attrs.get("is_superuser", is_superuser):
            raise serializers.ValidationError({"is_superuser": "Superuser role requires superuser status."})

        if employee_profile_data is None or remove_employee_profile:
            return attrs

        designation = employee_profile_data.get("designation")
        salary = employee_profile_data.get("salary")

        if self.instance is not None and hasattr(self.instance, "employee_profile"):
            if designation in (None, ""):
                designation = self.instance.employee_profile.designation
            if salary is None:
                salary = self.instance.employee_profile.salary

        if not str(designation or "").strip():
            raise serializers.ValidationError({"designation": "Designation is required for an employee profile."})
        if salary is None:
            raise serializers.ValidationError({"salary": "Salary is required for an employee profile."})

        return attrs

    def _upsert_employee_profile(self, user, employee_profile_data):
        designation = str(employee_profile_data.get("designation", "")).strip()
        salary = employee_profile_data.get("salary")

        employee_profile, _ = Employee.objects.get_or_create(
            user=user,
            defaults={"designation": designation, "salary": salary},
        )
        employee_profile.designation = designation
        employee_profile.salary = salary
        employee_profile.save()


class EmployeeSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "designation",
            "salary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_email", "user_name", "created_at", "updated_at"]

    def validate_user(self, value):
        qs = Employee.objects.filter(user=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This user already has an employee profile.")
        return value

    def validate_designation(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Designation cannot be empty.")
        return cleaned

    def get_user_name(self, obj):
        full_name = f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip()
        return full_name or obj.user.email
