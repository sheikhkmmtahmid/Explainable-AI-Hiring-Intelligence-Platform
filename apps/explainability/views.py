from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ExplanationReport
from .serializers import ExplanationReportSerializer
from .services import generate_explanation


def _check_match_result_access(user, match_result_id):
    from apps.matching.models import MatchResult

    if user.is_platform_staff:
        return
    match_result = get_object_or_404(MatchResult.objects.select_related("job"), pk=match_result_id)
    if match_result.job.organization_id != user.organization_id:
        raise PermissionDenied("You do not have access to this match result.")


class ExplanationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _serialize(self, match_result_id):
        report = ExplanationReport.objects.select_related("match_result").get(
            match_result_id=match_result_id
        )
        return ExplanationReportSerializer(report).data

    def get(self, request, match_result_id):
        _check_match_result_access(request.user, match_result_id)
        try:
            return Response(self._serialize(match_result_id))
        except ExplanationReport.DoesNotExist:
            return Response({"detail": "No explanation yet."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, match_result_id):
        _check_match_result_access(request.user, match_result_id)
        # method is an internal detail; default to shap, accept override for power users
        method = request.data.get("method", "shap")
        generate_explanation(match_result_id, method=method)
        return Response(self._serialize(match_result_id), status=status.HTTP_201_CREATED)
