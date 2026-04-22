from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import MatchResult
from .serializers import MatchResultSerializer
from .tasks import batch_match_job_task


class MatchResultViewSet(ReadOnlyModelViewSet):
    serializer_class = MatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MatchResult.objects.select_related("candidate", "job")
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
        top_n = int(request.query_params.get("n", settings.TOP_N_CANDIDATES))
        results = MatchResult.objects.filter(job_id=job_id).order_by("rank")[:top_n]
        return Response(MatchResultSerializer(results, many=True).data)
