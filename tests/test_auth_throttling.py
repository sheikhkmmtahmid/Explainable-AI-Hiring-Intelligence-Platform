import pytest

from apps.accounts.views import ChangePasswordView, LoginView, RegisterView


@pytest.mark.django_db
def test_login_throttled_after_configured_rate(factory):
    view = LoginView.as_view()
    statuses = []
    for _ in range(13):
        req = factory.post("/api/v1/auth/login/", {"username": "nope", "password": "wrong"}, format="json")
        resp = view(req)
        statuses.append(resp.status_code)
    # Rate is 10/min (see REST_FRAMEWORK.DEFAULT_THROTTLE_RATES) -- first 10
    # attempts get a real auth response, the rest get throttled.
    assert statuses[:10] == [401] * 10
    assert all(s == 429 for s in statuses[10:])


@pytest.mark.django_db
def test_register_throttled_after_configured_rate(factory):
    view = RegisterView.as_view()
    statuses = []
    for i in range(7):
        req = factory.post("/api/v1/auth/register/", {
            "username": f"newuser{i}", "email": f"newuser{i}@test.com",
            "password": "Str0ngPassw0rd!", "password_confirm": "Str0ngPassw0rd!",
        }, format="json")
        resp = view(req)
        statuses.append(resp.status_code)
    # Rate is 5/min
    assert statuses.count(429) >= 1
    assert 429 not in statuses[:5]


@pytest.mark.django_db
def test_password_change_throttled(factory, recruiter_a):
    from rest_framework.test import force_authenticate

    view = ChangePasswordView.as_view()
    statuses = []
    for _ in range(7):
        req = factory.post("/api/v1/auth/change-password/", {
            "old_password": "wrong", "new_password": "whatever",
        }, format="json")
        force_authenticate(req, user=recruiter_a)
        resp = view(req)
        statuses.append(resp.status_code)
    assert 429 in statuses
