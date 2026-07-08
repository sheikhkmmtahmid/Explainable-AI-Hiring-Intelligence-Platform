from django.urls import path
from .views import (
    SkillTaxonomyListView, JobRoleTemplateListView,
    ProposeSkillView, PendingSkillListView, PendingSkillReviewView,
)

urlpatterns = [
    path("skills/", SkillTaxonomyListView.as_view(), name="skill-taxonomy"),
    path("skills/propose/", ProposeSkillView.as_view(), name="skill-propose"),
    path("roles/", JobRoleTemplateListView.as_view(), name="job-roles"),
    path("pending-skills/", PendingSkillListView.as_view(), name="pending-skill-list"),
    path("pending-skills/<int:pk>/review/", PendingSkillReviewView.as_view(), name="pending-skill-review"),
]
