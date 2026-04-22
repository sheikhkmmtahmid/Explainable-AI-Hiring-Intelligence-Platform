from django.urls import path
from .views import TriggerIngestionView, IngestionRunListView

urlpatterns = [
    path("trigger/", TriggerIngestionView.as_view(), name="trigger-ingestion"),
    path("runs/", IngestionRunListView.as_view(), name="ingestion-runs"),
]
