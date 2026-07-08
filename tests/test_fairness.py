import pytest


@pytest.mark.django_db
class TestFairnessBasis:
    def test_falls_back_to_ai_rank_when_no_real_decisions_exist(self, job_a, candidate):
        from apps.matching.models import MatchResult
        from apps.fairness.models import FairnessReport
        from apps.fairness.services import compute_fairness_report

        MatchResult.objects.create(
            candidate=candidate, job=job_a, overall_score=0.8, rank=1,
            semantic_score=0.8, skill_overlap_score=0.8, experience_score=0.8, education_score=0.8,
        )
        result = compute_fairness_report(job_a.id, "gender")
        assert result["basis"] == FairnessReport.Basis.AI_RANK_PROVISIONAL

    def test_uses_real_decisions_once_applications_are_resolved(self, job_a, candidate):
        from apps.applications.models import Application
        from apps.fairness.models import FairnessReport
        from apps.fairness.services import compute_fairness_report

        Application.objects.create(candidate=candidate, job=job_a, status=Application.Status.SHORTLISTED)
        result = compute_fairness_report(job_a.id, "gender")
        assert result["basis"] == FairnessReport.Basis.ACTUAL_DECISIONS

    def test_pending_applications_excluded_from_decision_basis(self, job_a, candidate):
        """Applied/screening aren't real employer decisions -- if that's
        ALL that exists, it should still fall back to the AI-rank estimate
        rather than treat 'not yet decided' as a resolved outcome."""
        from apps.applications.models import Application
        from apps.matching.models import MatchResult
        from apps.fairness.models import FairnessReport
        from apps.fairness.services import compute_fairness_report

        Application.objects.create(candidate=candidate, job=job_a, status=Application.Status.APPLIED)
        MatchResult.objects.create(
            candidate=candidate, job=job_a, overall_score=0.5, rank=1,
            semantic_score=0.5, skill_overlap_score=0.5, experience_score=0.5, education_score=0.5,
        )
        result = compute_fairness_report(job_a.id, "gender")
        assert result["basis"] == FairnessReport.Basis.AI_RANK_PROVISIONAL
