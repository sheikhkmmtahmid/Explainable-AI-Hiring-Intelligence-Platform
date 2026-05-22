from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "password_confirm",
            "role", "organisation", "phone", "country",
        ]
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "role", "organisation", "phone", "country", "timezone",
            "is_verified", "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_verified"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Admin can create users of any role."""
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "role", "organisation", "phone", "country"]
        extra_kwargs = {"email": {"required": True}, "role": {"required": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ManagerCreateUserSerializer(serializers.ModelSerializer):
    """Manager (recruiter) can create recruiter or candidate users only."""
    password = serializers.CharField(write_only=True, validators=[validate_password])

    ALLOWED_ROLES = [User.Role.RECRUITER, User.Role.CANDIDATE]

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "role", "organisation", "phone", "country"]
        extra_kwargs = {"email": {"required": True}, "role": {"required": True}}

    def validate_role(self, value):
        if value not in self.ALLOWED_ROLES:
            raise serializers.ValidationError("Managers can only create recruiter or candidate accounts.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
