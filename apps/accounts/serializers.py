from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer
from .models import User


def _get_or_create_organization(name: str) -> Organization:
    name = name.strip()
    slug = slugify(name)
    org, _ = Organization.objects.get_or_create(slug=slug, defaults={"name": name})
    return org


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    # Self-service signup collects a company name, not an org ID -- creates
    # the Organization on the fly if it doesn't exist yet. Only meaningful
    # for roles that actually belong to a company (not candidates).
    organization_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "password_confirm",
            "role", "organization_name", "phone", "country",
        ]
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        role = attrs.get("role", User.Role.CANDIDATE)
        org_name = attrs.get("organization_name", "").strip()
        if role != User.Role.CANDIDATE and not org_name:
            raise serializers.ValidationError({"organization_name": "Company name is required for this role."})
        return attrs

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name", "").strip()
        if org_name:
            validated_data["organization"] = _get_or_create_organization(org_name)
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    is_platform_staff = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "role", "organization", "is_platform_staff", "phone", "country", "timezone",
            "is_verified", "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_verified"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Platform staff can create users of any role, for any organization."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    organization_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "role", "organization_name", "phone", "country"]
        extra_kwargs = {"email": {"required": True}, "role": {"required": True}}

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name", "").strip()
        if org_name:
            validated_data["organization"] = _get_or_create_organization(org_name)
        return User.objects.create_user(**validated_data)


class ManagerCreateUserSerializer(serializers.ModelSerializer):
    """
    Manager (org admin/recruiter) can create recruiter or candidate users
    only, and only within their own organization -- organization is never
    accepted from the client here, it's forced server-side in the view to
    request.user.organization so a manager can never add someone into a
    different company's account.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])

    ALLOWED_ROLES = [User.Role.RECRUITER, User.Role.CANDIDATE]

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "role", "phone", "country"]
        extra_kwargs = {"email": {"required": True}, "role": {"required": True}}

    def validate_role(self, value):
        if value not in self.ALLOWED_ROLES:
            raise serializers.ValidationError("Managers can only create recruiter or candidate accounts.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
