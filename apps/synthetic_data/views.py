from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .generators import BIAS_SCENARIOS
from .models import SyntheticGenerationRun
from .tasks import (
    generate_synthetic_candidates_task,
    generate_synthetic_jobs_task,
    generate_synthetic_applications_task,
)


class GenerateSyntheticView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        kind = request.data.get("kind", "candidates")
        count = int(request.data.get("count", 100))
        count = min(count, 5000)

        if kind == "candidates":
            generate_synthetic_candidates_task.delay(count)
        elif kind == "jobs":
            generate_synthetic_jobs_task.delay(count)
        elif kind == "applications":
            scenario = request.data.get("scenario", "no_bias")
            if scenario not in BIAS_SCENARIOS:
                return Response(
                    {"detail": f"Unknown scenario. Valid: {list(BIAS_SCENARIOS.keys())}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            apps_per = int(request.data.get("applications_per_candidate", 3))
            generate_synthetic_applications_task.delay(
                scenario_key=scenario,
                applications_per_candidate=apps_per,
            )
            return Response(
                {"detail": f"Generating synthetic applications with scenario '{scenario}'..."},
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                {"detail": "kind must be 'candidates', 'jobs', or 'applications'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": f"Generating {count} synthetic {kind}..."},
            status=status.HTTP_202_ACCEPTED,
        )


class BiasScenarioListView(APIView):
    """List all available bias scenarios and their descriptions."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = [
            {
                "key": key,
                "name": scenario.name,
                "description": scenario.description,
                "attribute": scenario.attribute,
                "base_shortlist_rate": scenario.base_shortlist_rate,
                "group_multipliers": scenario.group_multipliers,
            }
            for key, scenario in BIAS_SCENARIOS.items()
        ]
        return Response(data)


class SyntheticRunListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        runs = SyntheticGenerationRun.objects.order_by("-created_at")[:20]
        data = [
            {
                "id": r.id, "kind": r.kind, "status": r.status,
                "count_requested": r.count_requested, "count_created": r.count_created,
                "created_at": r.created_at,
            }
            for r in runs
        ]
        return Response(data)
