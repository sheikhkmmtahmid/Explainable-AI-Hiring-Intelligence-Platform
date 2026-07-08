import pytest
from rest_framework.test import force_authenticate


@pytest.fixture
def growth_plan(db):
    from apps.billing.models import Plan
    return Plan.objects.create(
        name="Growth", slug="growth-test", price="99.00", currency="USD",
        max_active_jobs=25, max_seats=15,
    )


@pytest.fixture
def manual_provider(db):
    from apps.billing.models import PaymentProvider
    provider, _ = PaymentProvider.objects.get_or_create(
        code="manual", defaults={"name": "Bank Transfer / Other", "is_automated": False},
    )
    return provider


@pytest.mark.django_db
class TestManualBillingFlow:
    def test_full_manual_subscribe_submit_approve_flow(
        self, factory, admin_a, platform_staff, growth_plan, manual_provider
    ):
        from apps.billing.models import Payment, Subscription
        from apps.billing.views import PendingPaymentReviewListView, ReviewPaymentView, SubmitPaymentProofView, SubscribeView

        # 1. Org admin starts a subscription via the manual provider.
        subscribe_view = SubscribeView.as_view()
        req = factory.post("/api/v1/billing/subscribe/", {
            "plan_id": growth_plan.id, "provider_code": "manual",
        }, format="json")
        force_authenticate(req, user=admin_a)
        resp = subscribe_view(req)
        assert resp.status_code == 201
        assert resp.data["requires_proof"] is True
        payment_id = resp.data["payment_id"]

        payment = Payment.objects.get(id=payment_id)
        assert payment.status == Payment.Status.PENDING

        # 2. Org admin submits a payment reference.
        proof_view = SubmitPaymentProofView.as_view()
        req2 = factory.post(f"/api/v1/billing/payments/{payment_id}/submit-proof/", {
            "proof_note": "Paid via bank transfer", "external_reference": "REF-123",
        }, format="json")
        force_authenticate(req2, user=admin_a)
        resp2 = proof_view(req2, payment_id=payment_id)
        assert resp2.status_code == 200
        assert resp2.data["status"] == "submitted"

        # 3. Platform staff sees it queued for review.
        list_view = PendingPaymentReviewListView.as_view()
        req3 = factory.get("/api/v1/billing/payments/pending-review/")
        force_authenticate(req3, user=platform_staff)
        resp3 = list_view(req3)
        assert resp3.data["count"] == 1

        # 4. Platform staff approves -- subscription activates.
        review_view = ReviewPaymentView.as_view()
        req4 = factory.post(f"/api/v1/billing/payments/{payment_id}/review/", {"action": "approve"}, format="json")
        force_authenticate(req4, user=platform_staff)
        resp4 = review_view(req4, payment_id=payment_id)
        assert resp4.status_code == 200
        assert resp4.data["status"] == "succeeded"

        subscription = Subscription.objects.get(organization=admin_a.organization)
        assert subscription.status == Subscription.Status.ACTIVE
        assert subscription.plan_id == growth_plan.id

    def test_recruiter_cannot_manage_billing(self, factory, recruiter_a, growth_plan, manual_provider):
        from apps.billing.views import SubscribeView

        # DRF's dispatch() catches PermissionDenied and turns it into a
        # 403 response -- it doesn't propagate as a raw exception here.
        view = SubscribeView.as_view()
        req = factory.post("/api/v1/billing/subscribe/", {
            "plan_id": growth_plan.id, "provider_code": "manual",
        }, format="json")
        force_authenticate(req, user=recruiter_a)
        resp = view(req)
        assert resp.status_code == 403

    def test_unconfigured_provider_rejected(self, factory, admin_a, growth_plan):
        from apps.billing.models import PaymentProvider
        from apps.billing.views import SubscribeView

        stripe, _ = PaymentProvider.objects.get_or_create(
            code="stripe", defaults={"name": "Card (Stripe)", "is_automated": True},
        )
        view = SubscribeView.as_view()
        req = factory.post("/api/v1/billing/subscribe/", {
            "plan_id": growth_plan.id, "provider_code": "stripe",
        }, format="json")
        force_authenticate(req, user=admin_a)
        resp = view(req)
        # No STRIPE_SECRET_KEY configured in test settings -> rejected cleanly.
        assert resp.status_code == 400
