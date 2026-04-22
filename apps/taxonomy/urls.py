from django.urls import path
from .views import SkillTaxonomyListView, JobRoleTemplateListView

urlpatterns = [
    path("skills/", SkillTaxonomyListView.as_view(), name="skill-taxonomy"),
    path("roles/", JobRoleTemplateListView.as_view(), name="job-roles"),
]
