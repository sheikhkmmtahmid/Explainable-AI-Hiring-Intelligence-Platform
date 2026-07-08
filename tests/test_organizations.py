import pytest
from rest_framework.test import force_authenticate

from apps.organizations.views import MyOrganizationView


@pytest.mark.django_db
class TestMyOrganization:
    def test_admin_can_update_own_org_country(self, factory, admin_a, org_a):
        view = MyOrganizationView.as_view()
        req = factory.patch("/api/v1/organizations/me/", {"country": "BD"}, format="json")
        force_authenticate(req, user=admin_a)
        resp = view(req)
        assert resp.status_code == 200
        org_a.refresh_from_db()
        assert org_a.country == "BD"

    def test_recruiter_cannot_update_org(self, factory, recruiter_a):
        view = MyOrganizationView.as_view()
        req = factory.patch("/api/v1/organizations/me/", {"country": "BD"}, format="json")
        force_authenticate(req, user=recruiter_a)
        resp = view(req)
        assert resp.status_code == 403

    def test_platform_staff_without_org_gets_404_on_get(self, factory, platform_staff):
        view = MyOrganizationView.as_view()
        req = factory.get("/api/v1/organizations/me/")
        force_authenticate(req, user=platform_staff)
        resp = view(req)
        assert resp.status_code == 404
