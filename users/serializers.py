from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    salary = serializers.DecimalField(source="employee_profile.salary", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "first_name",
            "last_name",
            "salary",
            "password",
            "is_staff",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_staff"]

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

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance
