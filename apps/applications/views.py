from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Application, ApplicationNote, InterviewSlot
from .serializers import ApplicationNoteSerializer, ApplicationSerializer, InterviewSlotSerializer


class ApplicationViewSet(ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["candidate__full_name", "job__title", "job__company"]

    def get_queryset(self):
        from apps.matching.models import MatchResult

        user = self.request.user
        qs = Application.objects.select_related("candidate", "job")
        if user.role == "candidate":
            qs = qs.filter(candidate__user=user)
        elif not user.is_platform_staff:
            # Which candidates applied where, and the recruiter notes/status
            # around that, is the single most sensitive thing in this
            # system -- must never cross an organization boundary.
            qs = qs.filter(job__organization_id=user.organization_id)

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        job_param = self.request.query_params.get("job")
        if job_param:
            qs = qs.filter(job_id=job_param)

        # Match scores live on MatchResult, not Application -- pull them in
        # via a correlated subquery so they're always current (a job that
        # gets re-matched later won't leave a stale score behind here).
        match_qs = MatchResult.objects.filter(
            candidate_id=OuterRef("candidate_id"), job_id=OuterRef("job_id")
        )
        qs = qs.annotate(
            match_result_id=Subquery(match_qs.values("id")[:1]),
            overall_match_score=Subquery(match_qs.values("overall_score")[:1]),
            semantic_score=Subquery(match_qs.values("semantic_score")[:1]),
            skill_overlap_score=Subquery(match_qs.values("skill_overlap_score")[:1]),
            experience_score=Subquery(match_qs.values("experience_score")[:1]),
            education_score=Subquery(match_qs.values("education_score")[:1]),
            rank=Subquery(match_qs.values("rank")[:1]),
        )
        return qs

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        from .models import ApplicationStatusHistory
        from .override_tracking import compute_override

        application = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Application.Status.values:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        previous_status = application.status
        application.status = new_status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        if new_status != previous_status:
            is_override, percentile = compute_override(application, new_status)
            ApplicationStatusHistory.objects.create(
                application=application, from_status=previous_status,
                to_status=new_status, changed_by=request.user,
                is_override=is_override, candidate_percentile_at_decision=percentile,
            )
        return Response(ApplicationSerializer(application).data)

    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(application=application, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def jobs_with_counts(self, request):
        """Powers the Applications job-filter combobox: only jobs that have
        at least one application, each with its applicant count, ordered by
        volume so the busiest / most relevant jobs surface first instead of
        an alphabetical firehose a recruiter has to scroll through."""
        from apps.jobs.models import JobPost

        user = request.user
        search = request.query_params.get("search", "").strip()
        qs = JobPost.objects.annotate(
            applicant_count=Count("applications")
        ).filter(applicant_count__gt=0)
        if not user.is_platform_staff:
            qs = qs.filter(organization_id=user.organization_id)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(company__icontains=search))
        qs = qs.order_by("-applicant_count", "title")[:50]
        return Response([
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "applicant_count": job.applicant_count,
            }
            for job in qs
        ])

    @action(detail=True, methods=["post"])
    def schedule_interview(self, request, pk=None):
        application = self.get_object()
        serializer = InterviewSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(application=application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
