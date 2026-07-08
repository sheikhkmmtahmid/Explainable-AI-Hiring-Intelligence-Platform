from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SkillTaxonomy, JobRoleTemplate, PendingSkill
from .serializers import SkillTaxonomySerializer, JobRoleTemplateSerializer, PendingSkillSerializer


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


class ProposeSkillView(APIView):
    """
    A recruiter typed a skill name that isn't in the taxonomy dropdown while
    posting a job. The name is usable for the job immediately (skill
    requirements are free-text, not FK-bound -- see JobSkillRequirement), but
    it's also checked against the taxonomy and, if not an exact match, queued
    as a PendingSkill so the platform's canonical skill list stays curated
    and de-duplicated over time instead of silently drifting.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from ml.nlp.skill_dedup import find_similar_skill

        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "name is required."}, status=status.HTTP_400_BAD_REQUEST)

        skill, score, match_type = find_similar_skill(name)
        if match_type == "exact":
            return Response({
                "status": "existing",
                "skill": SkillTaxonomySerializer(skill).data,
            })

        existing_pending = PendingSkill.objects.filter(
            proposed_name__iexact=name, status=PendingSkill.Status.PENDING
        ).first()
        if existing_pending:
            return Response({
                "status": "already_queued",
                "pending_skill": PendingSkillSerializer(existing_pending).data,
            })

        pending = PendingSkill.objects.create(
            proposed_name=name,
            source=PendingSkill.Source.USER_SUBMITTED,
            source_detail=f"submitted while posting a job by {request.user.get_full_name() or request.user.username}",
            status=PendingSkill.Status.PENDING,
            similar_existing_skill=skill,
            similarity_score=score,
            similarity_match_type=match_type or "",
            submitted_by=request.user,
        )
        return Response({
            "status": "possible_duplicate" if match_type else "new",
            "pending_skill": PendingSkillSerializer(pending).data,
        }, status=status.HTTP_201_CREATED)


def _require_admin(request):
    from apps.accounts.models import User
    return request.user.is_authenticated and request.user.role == User.Role.ADMIN


class PendingSkillListView(generics.ListAPIView):
    """Moderation queue. Admin-only -- taxonomy changes affect matching
    quality platform-wide, not just the submitting recruiter's own jobs."""
    serializer_class = PendingSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        status_param = self.request.query_params.get("status", PendingSkill.Status.PENDING)
        qs = PendingSkill.objects.select_related("similar_existing_skill", "submitted_by", "reviewed_by")
        if status_param != "all":
            qs = qs.filter(status=status_param)
        return qs

    def list(self, request, *args, **kwargs):
        if not _require_admin(request):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)


class PendingSkillReviewView(APIView):
    """POST {"action": "approve"|"reject", "category": "..." (optional, approve only)}"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not _require_admin(request):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        try:
            pending = PendingSkill.objects.get(pk=pk)
        except PendingSkill.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if pending.status != PendingSkill.Status.PENDING:
            return Response(
                {"detail": f"Already {pending.status}."}, status=status.HTTP_400_BAD_REQUEST
            )

        action = request.data.get("action")
        from .services import approve_pending_skill, reject_pending_skill

        if action == "approve":
            skill = approve_pending_skill(
                pending, reviewer=request.user, category=request.data.get("category")
            )
            return Response({
                "detail": "Approved.",
                "skill": SkillTaxonomySerializer(skill).data,
            })
        elif action == "reject":
            reject_pending_skill(pending, reviewer=request.user)
            return Response({"detail": "Rejected."})
        return Response({"detail": "action must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
