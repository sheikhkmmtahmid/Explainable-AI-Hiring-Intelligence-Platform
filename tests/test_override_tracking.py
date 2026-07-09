"""Tests for apps/applications/override_tracking.py."""
import pytest

from apps.applications.override_tracking import compute_override, get_override_summary


def _make_match_result(candidate, job, rank):
    from apps.matching.models import MatchResult
    return MatchResult.objects.create(
        candidate=candidate, job=job, rank=rank,
        overall_score=0.5, semantic_score=0.5, skill_overlap_score=0.5,
        experience_score=0.5, education_score=0.5,
    )


@pytest.mark.django_db
class TestComputeOverride:
    def test_no_match_result_is_not_computable(self, candidate, job_a):
        from apps.applications.models import Application
        app = Application.objects.create(candidate=candidate, job=job_a)
        is_override, percentile = compute_override(app, "shortlisted")
        assert is_override is None
        assert percentile is None

    def test_non_decision_status_is_not_computable(self, candidate, job_a):
        from apps.applications.models import Application
        app = Application.objects.create(candidate=candidate, job=job_a)
        _make_match_result(candidate, job_a, rank=1)
        for total in range(2):
            pass
        is_override, percentile = compute_override(app, "screening")
        assert is_override is None
        assert percentile is None

    def test_advancing_top_ranked_candidate_is_not_an_override(self, candidate, job_a):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate

        app = Application.objects.create(candidate=candidate, job=job_a)
        _make_match_result(candidate, job_a, rank=1)
        for i in range(9):
            other = Candidate.objects.create(full_name=f"Other {i}", email=f"other{i}@test.com")
            _make_match_result(other, job_a, rank=i + 2)

        is_override, percentile = compute_override(app, "shortlisted")
        assert is_override is False
        assert percentile == 0.0

    def test_advancing_bottom_ranked_candidate_is_an_override(self, candidate, job_a):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate

        for i in range(9):
            other = Candidate.objects.create(full_name=f"Other {i}", email=f"other{i}@test.com")
            _make_match_result(other, job_a, rank=i + 1)
        app = Application.objects.create(candidate=candidate, job=job_a)
        _make_match_result(candidate, job_a, rank=10)

        is_override, percentile = compute_override(app, "shortlisted")
        assert is_override is True
        assert percentile == pytest.approx(0.9)

    def test_rejecting_top_ranked_candidate_is_an_override(self, candidate, job_a):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate

        app = Application.objects.create(candidate=candidate, job=job_a)
        _make_match_result(candidate, job_a, rank=1)
        for i in range(9):
            other = Candidate.objects.create(full_name=f"Other {i}", email=f"other{i}@test.com")
            _make_match_result(other, job_a, rank=i + 2)

        is_override, percentile = compute_override(app, "rejected")
        assert is_override is True

    def test_rejecting_bottom_ranked_candidate_is_not_an_override(self, candidate, job_a):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate

        for i in range(9):
            other = Candidate.objects.create(full_name=f"Other {i}", email=f"other{i}@test.com")
            _make_match_result(other, job_a, rank=i + 1)
        app = Application.objects.create(candidate=candidate, job=job_a)
        _make_match_result(candidate, job_a, rank=10)

        is_override, percentile = compute_override(app, "rejected")
        assert is_override is False


@pytest.mark.django_db
class TestGetOverrideSummary:
    def test_summary_counts_only_computed_overrides(self, candidate, job_a, recruiter_a):
        from apps.applications.models import Application, ApplicationStatusHistory

        app = Application.objects.create(candidate=candidate, job=job_a)
        ApplicationStatusHistory.objects.create(
            application=app, from_status="applied", to_status="shortlisted",
            changed_by=recruiter_a, is_override=True, candidate_percentile_at_decision=0.9,
        )
        ApplicationStatusHistory.objects.create(
            application=app, from_status="shortlisted", to_status="hired",
            changed_by=recruiter_a, is_override=None, candidate_percentile_at_decision=None,
        )

        summary = get_override_summary(job_a.organization_id)
        assert summary["total_decisions"] == 1
        assert summary["override_count"] == 1
        assert summary["override_rate"] == 1.0

    def test_summary_sliced_by_protected_attribute(self, job_a, recruiter_a):
        from apps.applications.models import Application, ApplicationStatusHistory
        from apps.candidates.models import Candidate

        c1 = Candidate.objects.create(full_name="A", email="a1@test.com", gender="female")
        c2 = Candidate.objects.create(full_name="B", email="b1@test.com", gender="male")
        app1 = Application.objects.create(candidate=c1, job=job_a)
        app2 = Application.objects.create(candidate=c2, job=job_a)
        ApplicationStatusHistory.objects.create(
            application=app1, to_status="rejected", changed_by=recruiter_a,
            is_override=True, candidate_percentile_at_decision=0.1,
        )
        ApplicationStatusHistory.objects.create(
            application=app2, to_status="rejected", changed_by=recruiter_a,
            is_override=False, candidate_percentile_at_decision=0.9,
        )

        summary = get_override_summary(job_a.organization_id, protected_attribute="gender")
        assert summary["female"]["override_rate"] == 1.0
        assert summary["male"]["override_rate"] == 0.0
