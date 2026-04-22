from rest_framework import serializers
from .models import SkillTaxonomy, JobRoleTemplate


class SkillTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillTaxonomy
        fields = ["id", "name", "canonical_name", "category", "subcategory", "aliases", "is_technical"]


class JobRoleTemplateSerializer(serializers.ModelSerializer):
    core_skills = SkillTaxonomySerializer(many=True, read_only=True)

    class Meta:
        model = JobRoleTemplate
        fields = ["id", "title", "industry", "core_skills", "typical_education", "typical_experience_years"]
