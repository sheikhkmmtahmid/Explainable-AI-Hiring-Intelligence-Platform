from rest_framework import serializers

from .models import MatchResult


class MatchResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company = serializers.CharField(source="job.company", read_only=True)

    class Meta:
        model = MatchResult
        fields = [
            "id", "candidate", "candidate_name", "job", "job_title", "company",
            "overall_score", "semantic_score", "skill_overlap_score",
            "experience_score", "education_score", "rank", "computed_at",
        ]
        read_only_fields = fields
