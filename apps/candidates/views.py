from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import generics, permissions, parsers, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.parsing.tasks import parse_cv_task

from .models import Candidate, CandidateCV, CandidateSkill, CandidateExperience
from .serializers import (
    CandidateCVSerializer,
    CandidateCreateSerializer,
    CandidateExperienceSerializer,
    CandidateSerializer,
    CandidateSkillSerializer,
)
from .services import (
    anonymize_candidate,
    attach_cv,
    export_candidate_data,
    get_or_create_candidate_for_user,
)


class CandidateViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["full_name", "current_title", "city", "country", "email"]

    def get_queryset(self):
        user = self.request.user
        base = Candidate.objects.prefetch_related("skills", "experiences", "cvs")

        if user.is_platform_staff:
            qs = base.all()
        elif user.role in ("admin", "recruiter", "analyst"):
            # Private per company: visible if this org sourced the candidate
            # directly, or the candidate applied to one of this org's jobs.
            # Never the whole platform's candidate pool -- that would leak
            # one customer's applicant list to a competing customer.
            if not user.organization_id:
                qs = base.none()
            else:
                qs = base.filter(
                    Q(sourced_by_organization_id=user.organization_id)
                    | Q(applications__job__organization_id=user.organization_id)
                ).distinct()
        else:
            qs = base.filter(user=user)

        # Filter by is_synthetic if passed as query param
        is_synthetic = self.request.query_params.get("is_synthetic")
        if is_synthetic is not None:
            qs = qs.filter(is_synthetic=is_synthetic.lower() in ("true", "1"))
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CandidateCreateSerializer
        return CandidateSerializer

    @action(detail=True, methods=["post"], parser_classes=[parsers.MultiPartParser])
    def upload_cv(self, request, pk=None):
        candidate = self.get_object()
        file = request.FILES.get("cv")
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        cv = attach_cv(candidate, file, file.name)
        parse_cv_task.delay(cv.id)
        return Response(CandidateCVSerializer(cv).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="cvs/(?P<cv_id>[^/.]+)")
    def delete_cv(self, request, pk=None, cv_id=None):
        candidate = self.get_object()
        try:
            cv = candidate.cvs.get(id=cv_id)
        except candidate.cvs.model.DoesNotExist:
            return Response({"detail": "CV not found."}, status=status.HTTP_404_NOT_FOUND)
        cv.file.delete(save=False)
        cv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def skills(self, request, pk=None):
        candidate = self.get_object()
        skills = CandidateSkill.objects.filter(candidate=candidate)
        return Response(CandidateSkillSerializer(skills, many=True).data)

    @action(detail=True, methods=["get"])
    def experience(self, request, pk=None):
        candidate = self.get_object()
        exps = CandidateExperience.objects.filter(candidate=candidate)
        return Response(CandidateExperienceSerializer(exps, many=True).data)

    @action(detail=True, methods=["get"])
    def export_data(self, request, pk=None):
        """GDPR 'right to access' -- everything the platform holds about
        this person, as one downloadable document."""
        candidate = self.get_object()
        return Response(export_candidate_data(candidate))

    @action(detail=True, methods=["post"])
    def request_deletion(self, request, pk=None):
        """GDPR 'right to erasure'. Only the candidate themselves or
        platform staff can invoke this -- a hiring org seeing this
        candidate can't erase someone's identity on their own say-so, that
        would let a company destroy the evidence behind its own hiring
        decisions."""
        candidate = self.get_object()
        user = request.user
        is_self = candidate.user_id == user.id
        if not (is_self or user.is_platform_staff):
            raise PermissionDenied("Only the candidate or platform staff can request data deletion.")
        anonymize_candidate(candidate)
        return Response({"detail": "Personal data has been anonymized."})
