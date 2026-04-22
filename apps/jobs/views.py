from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.matching.tasks import generate_job_embedding_task

from .models import JobPost
from .serializers import JobPostCreateSerializer, JobPostListSerializer, JobPostSerializer
from .filters import JobPostFilter


class JobPostViewSet(ModelViewSet):
    queryset = JobPost.objects.prefetch_related("skill_requirements").select_related("created_by")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobPostFilter
    search_fields = ["title", "company", "description", "country", "city"]
    ordering_fields = ["posted_at", "created_at", "salary_min", "salary_max"]
    ordering = ["-posted_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return JobPostListSerializer
        if self.action in ("create", "update", "partial_update"):
            return JobPostCreateSerializer
        return JobPostSerializer

    def perform_create(self, serializer):
        job = serializer.save()
        _extract_skills_from_text(job)
        generate_job_embedding_task.delay(job.id)

    def perform_update(self, serializer):
        job = serializer.save()
        _extract_skills_from_text(job)
        generate_job_embedding_task.delay(job.id)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def extract_skills(self, request, pk=None):
        """Re-extract skills from job text and return updated skill list."""
        job = self.get_object()
        count = _extract_skills_from_text(job)
        from .serializers import JobPostSerializer
        return Response({
            "detail": f"Extracted {count} skills.",
            "skill_requirements": JobPostSerializer(job).data["skill_requirements"],
        })

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def close(self, request, pk=None):
        job = self.get_object()
        job.status = JobPost.Status.CLOSED
        job.save(update_fields=["status"])
        return Response({"detail": "Job closed."})

    @action(detail=False, methods=["get"])
    def active(self, request):
        qs = self.get_queryset().filter(status=JobPost.Status.ACTIVE)
        serializer = JobPostListSerializer(qs, many=True)
        return Response(serializer.data)


def _extract_skills_from_text(job) -> int:
    """Parse job text fields and save JobSkillRequirement rows. Returns count saved."""
    from apps.parsing.services import extract_skills_from_text
    from .models import JobSkillRequirement

    combined = " ".join(filter(None, [job.title, job.description, job.requirements, job.responsibilities]))
    if not combined.strip():
        return 0

    found = extract_skills_from_text(combined)
    if not found:
        return 0

    existing = set(
        JobSkillRequirement.objects.filter(job=job).values_list("skill_name", flat=True)
    )
    new_objs = [
        JobSkillRequirement(
            job=job,
            skill_name=s["skill_name"].strip().lower(),
            skill_category=s.get("category", "technical"),
            is_required=True,
        )
        for s in found
        if s["skill_name"].strip().lower() not in existing
    ]
    if new_objs:
        JobSkillRequirement.objects.bulk_create(new_objs, ignore_conflicts=True)
    return len(new_objs)
