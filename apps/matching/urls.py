from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MatchResultViewSet, TriggerMatchView, TopCandidatesView

router = DefaultRouter()
router.register("results", MatchResultViewSet, basename="match-result")

urlpatterns = [
    path("", include(router.urls)),
    path("trigger/<int:job_id>/", TriggerMatchView.as_view(), name="trigger-match"),
    path("top-candidates/<int:job_id>/", TopCandidatesView.as_view(), name="top-candidates"),
]
