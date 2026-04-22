from rest_framework import serializers
from .models import ExplanationReport


class ExplanationReportSerializer(serializers.ModelSerializer):
    overall_score = serializers.SerializerMethodField()
    semantic_score = serializers.SerializerMethodField()
    skill_overlap_score = serializers.SerializerMethodField()
    experience_score = serializers.SerializerMethodField()
    education_score = serializers.SerializerMethodField()

    class Meta:
        model = ExplanationReport
        fields = [
            "id", "match_result", "method",
            "feature_importances", "top_positive_factors", "top_negative_factors",
            "missing_skills", "matching_skills", "summary_text",
            "generated_at", "model_version",
            "overall_score", "semantic_score", "skill_overlap_score",
            "experience_score", "education_score",
        ]
        read_only_fields = fields

    def _mr(self, obj):
        return obj.match_result

    def get_overall_score(self, obj):
        return self._mr(obj).overall_score

    def get_semantic_score(self, obj):
        return self._mr(obj).semantic_score

    def get_skill_overlap_score(self, obj):
        return self._mr(obj).skill_overlap_score

    def get_experience_score(self, obj):
        return self._mr(obj).experience_score

    def get_education_score(self, obj):
        return self._mr(obj).education_score
