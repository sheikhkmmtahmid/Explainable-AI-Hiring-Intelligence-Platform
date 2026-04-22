from django.urls import path
from .views import FairnessReportView

urlpatterns = [
    path("<int:job_id>/", FairnessReportView.as_view(), name="fairness-report"),
]
