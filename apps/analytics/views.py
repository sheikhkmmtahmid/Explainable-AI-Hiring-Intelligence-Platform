from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_pipeline_snapshot, get_platform_summary


class PlatformSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(get_platform_summary())


class PipelineSnapshotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        return Response(build_pipeline_snapshot(job_id))
