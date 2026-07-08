import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIRequestFactory


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """DRF's ScopedRateThrottle tracks attempt counts in Django's cache --
    clear it before every test so throttle tests don't bleed into each
    other or into unrelated tests hitting the same endpoint."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def org_a(db):
    from apps.organizations.models import Organization
    return Organization.objects.create(name="Org A", slug="org-a", country="US")


@pytest.fixture
def org_b(db):
    from apps.organizations.models import Organization
    return Organization.objects.create(name="Org B", slug="org-b", country="BD")


@pytest.fixture
def recruiter_a(org_a):
    from apps.accounts.models import User
    return User.objects.create_user(
        username="recruiter_a", email="a@test.com", password="testpass123",
        role="recruiter", organization=org_a,
    )


@pytest.fixture
def admin_a(org_a):
    from apps.accounts.models import User
    return User.objects.create_user(
        username="admin_a", email="admin_a@test.com", password="testpass123",
        role="admin", organization=org_a,
    )


@pytest.fixture
def recruiter_b(org_b):
    from apps.accounts.models import User
    return User.objects.create_user(
        username="recruiter_b", email="b@test.com", password="testpass123",
        role="recruiter", organization=org_b,
    )


@pytest.fixture
def platform_staff(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        username="platform_staff", email="staff@test.com", password="testpass123",
        role="admin", is_superuser=True, is_staff=True,
    )


@pytest.fixture
def job_a(org_a, recruiter_a):
    from apps.jobs.models import JobPost
    return JobPost.objects.create(
        title="Org A Job", company="Org A", description="desc",
        organization=org_a, created_by=recruiter_a, source="manual",
        external_id="test-job-a", posted_at=timezone.now(),
    )


@pytest.fixture
def job_b(org_b, recruiter_b):
    from apps.jobs.models import JobPost
    return JobPost.objects.create(
        title="Org B Job", company="Org B", description="desc",
        organization=org_b, created_by=recruiter_b, source="manual",
        external_id="test-job-b", posted_at=timezone.now(),
    )


@pytest.fixture
def candidate(db):
    from apps.candidates.models import Candidate
    return Candidate.objects.create(full_name="Test Candidate", email="candidate@test.com")
