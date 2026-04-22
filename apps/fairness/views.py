from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FairnessReport, SubgroupMetric
from .serializers import FairnessReportSerializer
from .services import compute_fairness_report

ALLOWED_ATTRIBUTES = ["gender", "age_range", "ethnicity", "disability_status"]


class FairnessReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        reports = FairnessReport.objects.filter(job_id=job_id).prefetch_related("subgroups")
        return Response(FairnessReportSerializer(reports, many=True).data)

    def post(self, request, job_id):
        attr = request.data.get("protected_attribute", "gender")
        if attr not in ALLOWED_ATTRIBUTES:
            return Response(
                {"detail": f"Attribute must be one of {ALLOWED_ATTRIBUTES}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.matching.models import MatchResult
        if not MatchResult.objects.filter(job_id=job_id).exists():
            return Response(
                {"detail": "No matching results found for this job. Run matching first before generating a fairness report."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        compute_fairness_report(job_id, attr)
        # Return the freshly saved report via the serializer so the shape matches GET
        report = FairnessReport.objects.prefetch_related("subgroups").get(
            job_id=job_id, protected_attribute=attr
        )
        return Response(FairnessReportSerializer(report).data, status=status.HTTP_201_CREATED)
