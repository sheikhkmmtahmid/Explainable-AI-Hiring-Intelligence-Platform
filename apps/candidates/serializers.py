from rest_framework import serializers

from .models import Candidate, CandidateCV, CandidateEmbedding, CandidateExperience, CandidateSkill


class CandidateSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateSkill
        fields = ["id", "skill_name", "skill_category", "proficiency", "years_used", "source"]


class CandidateExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateExperience
        fields = [
            "id", "job_title", "company", "location",
            "start_date", "end_date", "is_current", "description",
        ]


class CandidateCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateCV
        fields = ["id", "file", "original_filename", "file_type", "is_primary", "parsed_at", "uploaded_at"]
        read_only_fields = ["original_filename", "file_type", "parsed_at"]


class CandidateSerializer(serializers.ModelSerializer):
    skills = CandidateSkillSerializer(many=True, read_only=True)
    experiences = CandidateExperienceSerializer(many=True, read_only=True)
    cvs = CandidateCVSerializer(many=True, read_only=True)

    class Meta:
        model = Candidate
        fields = [
            "id", "full_name", "email", "phone",
            "country", "city", "region", "remote_preference",
            "current_title", "years_of_experience", "seniority_level", "summary",
            "highest_education", "education_field",
            "availability_status", "expected_salary_min", "expected_salary_max", "salary_currency",
            "is_synthetic", "skills", "experiences", "cvs", "created_at",
        ]
        read_only_fields = ["id", "is_synthetic", "created_at"]


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",  # returned so the frontend can immediately use it (e.g. CV upload)
            "full_name", "email", "phone",
            "country", "city", "region", "remote_preference",
            "current_title", "years_of_experience", "seniority_level", "summary",
            "highest_education", "education_field",
            "availability_status", "expected_salary_min", "expected_salary_max", "salary_currency",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = self.context["request"].user
        # Only link the Django user to the candidate profile when the user IS the candidate.
        # Admins and recruiters create profiles on behalf of other people.
        if getattr(user, "role", None) == "candidate":
            return Candidate.objects.create(user=user, **validated_data)
        return Candidate.objects.create(**validated_data)
