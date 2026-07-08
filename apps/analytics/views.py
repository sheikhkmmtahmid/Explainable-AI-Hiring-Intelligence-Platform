from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matching.views import _check_job_access

from .services import build_pipeline_snapshot, get_platform_summary


class PlatformSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org_id = None if user.is_platform_staff else user.organization_id
        return Response(get_platform_summary(organization_id=org_id))


class PipelineSnapshotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        _check_job_access(request.user, job_id)
        return Response(build_pipeline_snapshot(job_id))
