from rest_framework import serializers

from .models import JobPost, JobSkillRequirement


class JobSkillRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSkillRequirement
        fields = ["id", "skill_name", "skill_category", "is_required", "min_years"]


class JobPostSerializer(serializers.ModelSerializer):
    skill_requirements = JobSkillRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = JobPost
        fields = [
            "id", "title", "company", "description", "requirements", "responsibilities",
            "country", "city", "region", "work_model",
            "industry", "job_function", "employment_type", "experience_level",
            "salary_min", "salary_max", "salary_currency",
            "status", "posted_at", "expires_at",
            "source", "external_url", "is_synthetic",
            "skill_requirements", "created_at",
        ]
        read_only_fields = ["id", "is_synthetic", "source", "created_at"]


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

    def create(self, validated_data):
        from uuid import uuid4
        from django.utils import timezone
        user = self.context["request"].user
        return JobPost.objects.create(
            created_by=user,
            source="manual",
            external_id=f"manual_{uuid4().hex[:16]}",
            posted_at=timezone.now(),
            **validated_data,
        )


class JobPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    class Meta:
        model = JobPost
        fields = [
            "id", "title", "company", "country", "city", "work_model",
            "employment_type", "experience_level", "salary_min", "salary_max",
            "salary_currency", "status", "posted_at", "source",
        ]
