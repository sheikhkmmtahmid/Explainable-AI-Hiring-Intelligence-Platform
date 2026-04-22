from django.urls import path
from .views import GenerateSyntheticView, SyntheticRunListView, BiasScenarioListView

urlpatterns = [
    path("generate/", GenerateSyntheticView.as_view(), name="generate-synthetic"),
    path("runs/", SyntheticRunListView.as_view(), name="synthetic-runs"),
    path("scenarios/", BiasScenarioListView.as_view(), name="bias-scenarios"),
]
