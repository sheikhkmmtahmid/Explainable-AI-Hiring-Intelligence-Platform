from django.urls import path
from .views import FairnessReportView, OverrideSummaryView

urlpatterns = [
    path("overrides/", OverrideSummaryView.as_view(), name="fairness-overrides"),
    path("<int:job_id>/", FairnessReportView.as_view(), name="fairness-report"),
]
