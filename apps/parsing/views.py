from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ParseJob


class ParseJobStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cv_id):
        job = ParseJob.objects.filter(cv_id=cv_id).order_by("-created_at").first()
        if not job:
            return Response({"status": "not_started"})
        return Response({
            "status": job.status,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": job.error_message or None,
        })
