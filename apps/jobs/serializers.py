from rest_framework import serializers

from .models import JobPost, JobSkillRequirement


class JobSkillRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSkillRequirement
        fields = ["id", "skill_name", "skill_category", "is_required", "min_years"]


class JobPostSerializer(serializers.ModelSerializer):
    skill_requirements = JobSkillRequirementSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True, default=None)

    class Meta:
        model = JobPost
        fields = [
            "id", "organization", "organization_name",
            "title", "company", "description", "requirements", "responsibilities",
            "country", "city", "region", "work_model",
            "industry", "job_function", "employment_type", "experience_level",
            "salary_min", "salary_max", "salary_currency",
            "status", "posted_at", "expires_at",
            "source", "external_url", "is_synthetic",
            "skill_requirements", "created_at",
        ]
        read_only_fields = ["id", "organization", "is_synthetic", "source", "created_at"]


class JobPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = [
            "id",
            "title", "company", "description", "requirements", "responsibilities",
            "country", "city", "region", "work_model",
            "industry", "job_function", "employment_type", "experience_level",
            "salary_min", "salary_max", "salary_currency",
            "status", "expires_at",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_platform_staff and user.organization_id is None:
            raise serializers.ValidationError(
                "Your account isn't linked to an organization yet -- can't post a job."
            )
        return attrs

    def create(self, validated_data):
        from uuid import uuid4
        from django.utils import timezone
        user = self.context["request"].user
        return JobPost.objects.create(
            created_by=user,
            organization=user.organization,
            source="manual",
            external_id=f"manual_{uuid4().hex[:16]}",
            posted_at=timezone.now(),
            **validated_data,
        )


class JobPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    organization_name = serializers.CharField(source="organization.name", read_only=True, default=None)

    class Meta:
        model = JobPost
        fields = [
            "id", "organization_name", "title", "company", "country", "city", "work_model",
            "employment_type", "experience_level", "salary_min", "salary_max",
            "salary_currency", "status", "posted_at", "source", "is_synthetic",
        ]
