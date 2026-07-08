from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "country", "industry", "is_active", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]
