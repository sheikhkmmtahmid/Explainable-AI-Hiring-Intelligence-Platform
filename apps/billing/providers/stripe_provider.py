import logging

from django.conf import settings

from .base import PaymentProviderBase

logger = logging.getLogger(__name__)


class StripeProvider(PaymentProviderBase):
    code = "stripe"

    def is_configured(self) -> bool:
        return bool(settings.STRIPE_SECRET_KEY)

    def start_checkout(self, *, organization, plan, payment) -> dict:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": plan.currency.lower(),
                    "product_data": {"name": f"{plan.name} plan"},
                    "recurring": {"interval": "year" if plan.billing_interval == "yearly" else "month"},
                    "unit_amount": int(plan.price * 100),
                },
                "quantity": 1,
            }],
            success_url=settings.BILLING_SUCCESS_URL,
            cancel_url=settings.BILLING_CANCEL_URL,
            client_reference_id=str(organization.id),
            metadata={"organization_id": organization.id, "payment_id": payment.id},
        )
        payment.external_reference = session.id
        payment.save(update_fields=["external_reference"])
        return {"redirect_url": session.url}

    def handle_webhook(self, request):
        """Verifies the Stripe signature and, on checkout.session.completed,
        marks the matching Payment succeeded and activates the subscription.
        Returns the Payment that was resolved, or None."""
        import stripe
        from django.utils import timezone
        from apps.billing.models import Payment, Subscription

        stripe.api_key = settings.STRIPE_SECRET_KEY
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            logger.warning("Stripe webhook signature verification failed: %s", exc)
            return None

        if event["type"] != "checkout.session.completed":
            return None

        session = event["data"]["object"]
        payment_id = session.get("metadata", {}).get("payment_id")
        if not payment_id:
            return None

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return None

        payment.status = Payment.Status.SUCCEEDED
        payment.external_reference = session.get("id", payment.external_reference)
        payment.save(update_fields=["status", "external_reference"])

        if payment.subscription_id:
            sub = payment.subscription
            sub.status = Subscription.Status.ACTIVE
            sub.current_period_start = timezone.now()
            sub.save(update_fields=["status", "current_period_start"])

        return payment
