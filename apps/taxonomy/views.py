from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter

from .models import SkillTaxonomy, JobRoleTemplate
from .serializers import SkillTaxonomySerializer, JobRoleTemplateSerializer


class SkillTaxonomyListView(generics.ListAPIView):
    queryset = SkillTaxonomy.objects.all()
    serializer_class = SkillTaxonomySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ["name", "canonical_name", "category"]


class JobRoleTemplateListView(generics.ListAPIView):
    queryset = JobRoleTemplate.objects.all()
    serializer_class = JobRoleTemplateSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ["title", "industry"]
