from rest_framework import serializers
from .models import SkillTaxonomy, JobRoleTemplate, PendingSkill


class SkillTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillTaxonomy
        fields = ["id", "name", "canonical_name", "category", "subcategory", "aliases", "is_technical"]


class JobRoleTemplateSerializer(serializers.ModelSerializer):
    core_skills = SkillTaxonomySerializer(many=True, read_only=True)

    class Meta:
        model = JobRoleTemplate
        fields = ["id", "title", "industry", "core_skills", "typical_education", "typical_experience_years"]


class PendingSkillSerializer(serializers.ModelSerializer):
    similar_existing_skill = SkillTaxonomySerializer(read_only=True)
    submitted_by_name = serializers.CharField(source="submitted_by.get_full_name", read_only=True, default="")
    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True, default="")

    class Meta:
        model = PendingSkill
        fields = [
            "id", "proposed_name", "category", "source", "source_detail", "status",
            "similar_existing_skill", "similarity_score", "similarity_match_type",
            "submitted_by_name", "reviewed_by_name", "reviewed_at", "created_at",
        ]
        read_only_fields = fields
