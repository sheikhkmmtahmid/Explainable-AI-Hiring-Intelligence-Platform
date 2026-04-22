from django.urls import path
from .views import ExplanationView

urlpatterns = [
    path("<int:match_result_id>/", ExplanationView.as_view(), name="explanation"),
]
