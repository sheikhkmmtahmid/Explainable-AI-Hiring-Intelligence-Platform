import pytest
from rest_framework.test import force_authenticate

from apps.candidates.views import CandidateViewSet


@pytest.mark.django_db
class TestGDPRExportAndDeletion:
    def test_export_includes_profile_data(self, factory, platform_staff, candidate):
        view = CandidateViewSet.as_view({"get": "export_data"})
        req = factory.get(f"/api/v1/candidates/{candidate.id}/export_data/")
        force_authenticate(req, user=platform_staff)
        resp = view(req, pk=candidate.id)
        assert resp.status_code == 200
        assert resp.data["profile"]["full_name"] == candidate.full_name
        assert resp.data["profile"]["email"] == candidate.email

    def test_deletion_anonymizes_pii_but_keeps_protected_attributes(self, factory, platform_staff, candidate):
        candidate.gender = "female"
        candidate.ethnicity = "asian"
        candidate.save(update_fields=["gender", "ethnicity"])

        view = CandidateViewSet.as_view({"post": "request_deletion"})
        req = factory.post(f"/api/v1/candidates/{candidate.id}/request_deletion/")
        force_authenticate(req, user=platform_staff)
        resp = view(req, pk=candidate.id)
        assert resp.status_code == 200

        candidate.refresh_from_db()
        assert candidate.full_name.startswith("Deleted Candidate #")
        assert candidate.email.endswith("@deleted.invalid")
        # Protected attributes survive anonymization -- needed for fairness audits.
        assert candidate.gender == "female"
        assert candidate.ethnicity == "asian"

    def test_recruiter_cannot_request_deletion_for_others(self, factory, recruiter_a, org_a, candidate):
        # Make the candidate visible to recruiter_a (sourced by their own
        # org) so this test actually exercises the "visible but not
        # authorized to erase" check, not just a 404 for not seeing them.
        candidate.sourced_by_organization = org_a
        candidate.save(update_fields=["sourced_by_organization"])

        # DRF's dispatch() catches PermissionDenied and turns it into a
        # 403 response -- it doesn't propagate as a raw exception here.
        view = CandidateViewSet.as_view({"post": "request_deletion"})
        req = factory.post(f"/api/v1/candidates/{candidate.id}/request_deletion/")
        force_authenticate(req, user=recruiter_a)
        resp = view(req, pk=candidate.id)
        assert resp.status_code == 403
