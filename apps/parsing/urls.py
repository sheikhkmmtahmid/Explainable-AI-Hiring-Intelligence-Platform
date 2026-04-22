from django.urls import path
from .views import ParseJobStatusView

urlpatterns = [
    path("status/<int:cv_id>/", ParseJobStatusView.as_view(), name="parse-status"),
]
