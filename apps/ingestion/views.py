from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IngestionRun
from .tasks import ingest_adzuna_jobs_task


class TriggerIngestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        source = request.data.get("source", "adzuna")
        query = request.data.get("query", "software engineer")
        country = request.data.get("country", "gb")
        location = request.data.get("location", "")

        if source == "adzuna":
            ingest_adzuna_jobs_task.delay(query=query, country=country, location=location)
        else:
            return Response({"detail": f"Source '{source}' not supported yet."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": f"Ingestion from {source} queued."}, status=status.HTTP_202_ACCEPTED)


class IngestionRunListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        runs = IngestionRun.objects.order_by("-created_at")[:50]
        data = [
            {
                "id": r.id, "source": r.source, "status": r.status,
                "query": r.query, "jobs_created": r.jobs_created, "created_at": r.created_at,
            }
            for r in runs
        ]
        return Response(data)
