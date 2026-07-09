from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import MatchResult
from .serializers import MatchResultSerializer
from .tasks import batch_match_job_task


def _check_job_access(user, job_id):
    """Match results/rankings for a job are exactly as sensitive as the
    applications behind them -- must never cross an organization boundary."""
    from apps.jobs.models import JobPost

    if user.is_platform_staff:
        return
    job = get_object_or_404(JobPost, pk=job_id)
    if job.organization_id != user.organization_id:
        raise PermissionDenied("You do not have access to this job's match results.")


class MatchResultViewSet(ReadOnlyModelViewSet):
    serializer_class = MatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MatchResult.objects.select_related("candidate", "job")
        user = self.request.user
        if not user.is_platform_staff:
            qs = qs.filter(job__organization_id=user.organization_id)
        job_id = self.request.query_params.get("job")
        candidate_id = self.request.query_params.get("candidate")
        if job_id:
            qs = qs.filter(job_id=job_id)
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        return qs


class TriggerMatchView(APIView):
    """Trigger async batch matching for a specific job."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        _check_job_access(request.user, job_id)
        batch_match_job_task.delay(job_id)
        return Response(
            {"detail": f"Matching job {job_id} queued."},
            status=status.HTTP_202_ACCEPTED,
        )


class TopCandidatesView(APIView):
    """Return top-N ranked candidates for a job."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        from django.conf import settings
        _check_job_access(request.user, job_id)
        top_n = int(request.query_params.get("n", settings.TOP_N_CANDIDATES))
        results = MatchResult.objects.filter(job_id=job_id).order_by("rank")[:top_n]
        return Response(MatchResultSerializer(results, many=True).data)


def _resolve_organization_id(request):
    """An org-scoped user always resolves to their own organization. Platform
    staff have no organization of their own, so they resolve one from an
    explicit organization_id, or from a job_id (whichever job they're
    currently looking at on the fairness dashboard) -- matching how this
    view actually gets used, rather than forcing platform staff to look up
    and pass a raw organization id by hand."""
    user = request.user
    if not user.is_platform_staff:
        return user.organization_id

    org_id = request.query_params.get("organization_id")
    if org_id:
        return int(org_id)

    job_id = request.query_params.get("job_id")
    if job_id:
        from apps.jobs.models import JobPost
        job = JobPost.objects.filter(id=job_id).only("organization_id").first()
        return job.organization_id if job else None

    return None


class MatchingConfidenceView(APIView):
    """How much real decision data backs this organization's matching --
    see apps.matching.services.get_matching_confidence for what the tiers
    mean and why this exists (there is no per-org trained model yet, so
    every organization currently runs on the same fixed-weight scorer
    regardless of how much real history they have)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org_id = _resolve_organization_id(request)
        if not org_id:
            return Response(
                {"detail": "Could not determine an organization (pass job_id or organization_id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .services import get_matching_confidence
        return Response(get_matching_confidence(org_id))
