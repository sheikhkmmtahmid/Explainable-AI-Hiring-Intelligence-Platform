"""Tests for apps/matching/services.py::get_matching_confidence."""
import pytest

from apps.matching.services import get_matching_confidence


@pytest.mark.django_db
class TestGetMatchingConfidence:
    def test_no_real_decisions_is_no_data_tier(self, org_a):
        result = get_matching_confidence(org_a.id)
        assert result["real_decision_count"] == 0
        assert result["confidence_tier"] == "no_data"

    def test_synthetic_decisions_do_not_count(self, org_a, job_a, candidate):
        from apps.applications.models import Application
        Application.objects.create(candidate=candidate, job=job_a, status="hired", is_synthetic=True)
        result = get_matching_confidence(org_a.id)
        assert result["real_decision_count"] == 0
        assert result["confidence_tier"] == "no_data"

    def test_real_decisions_count_and_advance_tiers(self, org_a, job_a):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate

        for i in range(12):
            c = Candidate.objects.create(full_name=f"C{i}", email=f"c{i}@test.com")
            Application.objects.create(candidate=c, job=job_a, status="rejected", is_synthetic=False)

        result = get_matching_confidence(org_a.id)
        assert result["real_decision_count"] == 12
        assert result["confidence_tier"] == "early_signal"

    def test_non_decision_statuses_do_not_count(self, org_a, job_a, candidate):
        from apps.applications.models import Application
        Application.objects.create(candidate=candidate, job=job_a, status="applied", is_synthetic=False)
        result = get_matching_confidence(org_a.id)
        assert result["real_decision_count"] == 0
