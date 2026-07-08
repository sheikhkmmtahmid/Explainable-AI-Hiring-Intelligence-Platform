from rest_framework import serializers

from .models import Application, ApplicationNote, InterviewSlot


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company = serializers.CharField(source="job.company", read_only=True)

    # Match scores are NOT stored on Application -- they're annotated onto
    # the queryset live from MatchResult (see ApplicationViewSet.get_queryset)
    # so they can never go stale if the job gets re-matched later. These
    # declared fields just expose whatever the queryset annotated.
    match_result_id = serializers.IntegerField(read_only=True, allow_null=True)
    overall_match_score = serializers.FloatField(read_only=True, allow_null=True)
    semantic_score = serializers.FloatField(read_only=True, allow_null=True)
    skill_overlap_score = serializers.FloatField(read_only=True, allow_null=True)
    experience_score = serializers.FloatField(read_only=True, allow_null=True)
    education_score = serializers.FloatField(read_only=True, allow_null=True)
    rank = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Application
        fields = [
            "id", "candidate", "candidate_name", "job", "job_title", "company",
            "status", "applied_at", "updated_at",
            "match_result_id", "overall_match_score", "semantic_score", "skill_overlap_score",
            "experience_score", "education_score", "rank",
            "recruiter_notes", "reviewed_at",
        ]
        read_only_fields = ["id", "applied_at"]


class ApplicationNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = ApplicationNote
        fields = ["id", "author_name", "content", "created_at"]
        read_only_fields = ["id", "author_name", "created_at"]


class InterviewSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSlot
        fields = [
            "id", "scheduled_at", "duration_minutes", "interview_type",
            "meeting_link", "notes", "outcome", "created_at",
        ]
