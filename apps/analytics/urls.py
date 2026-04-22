from django.urls import path
from .views import PlatformSummaryView, PipelineSnapshotView

urlpatterns = [
    path("summary/", PlatformSummaryView.as_view(), name="platform-summary"),
    path("pipeline/<int:job_id>/", PipelineSnapshotView.as_view(), name="pipeline-snapshot"),
]
