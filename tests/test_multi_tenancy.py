import pytest
from django.core.exceptions import PermissionDenied
from rest_framework.test import force_authenticate


@pytest.mark.django_db
class TestApplicationIsolation:
    def test_recruiter_only_sees_own_org_applications(self, factory, recruiter_a, recruiter_b, job_a, candidate):
        from apps.applications.models import Application
        from apps.applications.views import ApplicationViewSet

        Application.objects.create(candidate=candidate, job=job_a)
        view = ApplicationViewSet.as_view({"get": "list"})

        req = factory.get("/api/v1/applications/")
        force_authenticate(req, user=recruiter_b)
        resp = view(req)
        assert resp.data["count"] == 0

        req2 = factory.get("/api/v1/applications/")
        force_authenticate(req2, user=recruiter_a)
        resp2 = view(req2)
        assert resp2.data["count"] == 1


@pytest.mark.django_db
class TestCandidateIsolation:
    def test_recruiter_only_sees_candidates_linked_to_own_org(self, factory, recruiter_a, recruiter_b, job_a, candidate):
        from apps.applications.models import Application
        from apps.candidates.views import CandidateViewSet

        Application.objects.create(candidate=candidate, job=job_a)
        view = CandidateViewSet.as_view({"get": "list"})

        req = factory.get(f"/api/v1/candidates/?search={candidate.full_name}")
        force_authenticate(req, user=recruiter_b)
        resp = view(req)
        names = [c["full_name"] for c in resp.data["results"]]
        assert candidate.full_name not in names

        req2 = factory.get(f"/api/v1/candidates/?search={candidate.full_name}")
        force_authenticate(req2, user=recruiter_a)
        resp2 = view(req2)
        names2 = [c["full_name"] for c in resp2.data["results"]]
        assert candidate.full_name in names2


@pytest.mark.django_db
class TestJobManagementIsolation:
    def test_recruiter_cannot_manage_other_orgs_job(self, factory, recruiter_a, recruiter_b, job_a):
        from apps.jobs.views import JobPostViewSet

        view = JobPostViewSet.as_view({"post": "close"})
        req = factory.post(f"/api/v1/jobs/{job_a.id}/close/")
        force_authenticate(req, user=recruiter_b)
        resp = view(req, pk=job_a.id)
        assert resp.status_code == 403

    def test_recruiter_can_manage_own_org_job(self, factory, recruiter_a, job_a):
        from apps.jobs.models import JobPost
        from apps.jobs.views import JobPostViewSet

        view = JobPostViewSet.as_view({"post": "close"})
        req = factory.post(f"/api/v1/jobs/{job_a.id}/close/")
        force_authenticate(req, user=recruiter_a)
        resp = view(req, pk=job_a.id)
        assert resp.status_code == 200
        job_a.refresh_from_db()
        assert job_a.status == JobPost.Status.CLOSED

    def test_public_active_job_listing_is_unscoped(self, factory, job_a, job_b):
        from apps.jobs.models import JobPost
        from apps.jobs.views import JobPostViewSet

        JobPost.objects.filter(id__in=[job_a.id, job_b.id]).update(status=JobPost.Status.ACTIVE)
        view = JobPostViewSet.as_view({"get": "list"})
        req = factory.get("/api/v1/jobs/")
        resp = view(req)
        ids = {j["id"] for j in resp.data["results"]}
        assert job_a.id in ids and job_b.id in ids


@pytest.mark.django_db
class TestMatchResultIsolation:
    def test_top_candidates_denied_across_orgs(self, factory, recruiter_b, job_a):
        from apps.matching.views import TopCandidatesView

        view = TopCandidatesView.as_view()
        req = factory.get(f"/api/v1/matching/top-candidates/{job_a.id}/")
        force_authenticate(req, user=recruiter_b)
        resp = view(req, job_id=job_a.id)
        assert resp.status_code == 403


@pytest.mark.django_db
class TestPlatformStaffBypass:
    def test_platform_staff_sees_all_orgs_applications(self, factory, platform_staff, job_a, job_b, candidate):
        from apps.applications.models import Application
        from apps.applications.views import ApplicationViewSet

        Application.objects.create(candidate=candidate, job=job_a)
        view = ApplicationViewSet.as_view({"get": "list"})
        req = factory.get("/api/v1/applications/")
        force_authenticate(req, user=platform_staff)
        resp = view(req)
        assert resp.data["count"] == 1
