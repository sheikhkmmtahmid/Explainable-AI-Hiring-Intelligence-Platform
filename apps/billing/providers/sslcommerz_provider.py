import logging

import requests
from django.conf import settings

from .base import PaymentProviderBase

logger = logging.getLogger(__name__)

SANDBOX_SESSION_URL = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
LIVE_SESSION_URL = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
SANDBOX_VALIDATION_URL = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
LIVE_VALIDATION_URL = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"


class SSLCommerzProvider(PaymentProviderBase):
    """
    Bangladesh's leading payment aggregator -- one integration bundles
    bKash, Nagad, Rocket, Dutch-Bangla mobile banking, and cards behind a
    single checkout page. This is deliberately used instead of integrating
    each mobile banking service separately: bKash/Nagad's own merchant
    APIs require a direct merchant agreement per service, which isn't
    realistic for every customer signing up -- SSLCommerz (or aamarPay/
    ShurjoPay, which follow the same shape) is how small/early platforms
    actually offer these rails in Bangladesh.
    """
    code = "sslcommerz"

    def is_configured(self) -> bool:
        return bool(settings.SSLCOMMERZ_STORE_ID and settings.SSLCOMMERZ_STORE_PASSWORD)

    def _session_url(self):
        return SANDBOX_SESSION_URL if settings.SSLCOMMERZ_SANDBOX else LIVE_SESSION_URL

    def _validation_url(self):
        return SANDBOX_VALIDATION_URL if settings.SSLCOMMERZ_SANDBOX else LIVE_VALIDATION_URL

    def start_checkout(self, *, organization, plan, payment) -> dict:
        from django.urls import reverse

        tran_id = f"org{organization.id}-payment{payment.id}"
        ipn_url = settings.BACKEND_BASE_URL.rstrip("/") + reverse("billing-webhook-sslcommerz")
        # The org's own contact details -- used for the SSLCommerz customer
        # fields it requires; not stored anywhere beyond this request.
        contact_name = organization.name
        contact_email = f"billing+org{organization.id}@{organization.slug}.invalid"

        payload = {
            "store_id": settings.SSLCOMMERZ_STORE_ID,
            "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
            "total_amount": str(payment.amount),
            "currency": payment.currency,
            "tran_id": tran_id,
            "success_url": settings.BILLING_SUCCESS_URL,
            "fail_url": settings.BILLING_CANCEL_URL,
            "cancel_url": settings.BILLING_CANCEL_URL,
            "ipn_url": ipn_url,
            "cus_name": contact_name,
            "cus_email": contact_email,
            "cus_phone": "N/A",
            "cus_add1": organization.country or "N/A",
            "cus_country": organization.country or "N/A",
            "product_category": "Subscription",
            "product_name": f"{plan.name} plan",
            "product_profile": "general",
            "value_a": str(payment.id),  # carried through to the IPN so we can match it back
        }
        try:
            resp = requests.post(self._session_url(), data=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("SSLCommerz session init failed: %s", exc)
            raise RuntimeError("Could not start SSLCommerz checkout -- please try again.") from exc

        gateway_url = data.get("GatewayPageURL")
        if not gateway_url:
            logger.error("SSLCommerz session init returned no GatewayPageURL: %s", data)
            raise RuntimeError("SSLCommerz did not return a payment page -- please try again.")

        payment.external_reference = tran_id
        payment.save(update_fields=["external_reference"])
        return {"redirect_url": gateway_url}

    def handle_ipn(self, post_data: dict):
        """Validates an IPN callback server-side against SSLCommerz's
        Order Validation API (never trust the IPN payload's own status
        field alone -- it can be spoofed) and resolves the matching
        Payment. Returns the Payment, or None."""
        from django.utils import timezone
        from apps.billing.models import Payment, Subscription

        val_id = post_data.get("val_id")
        payment_id = post_data.get("value_a")
        if not val_id or not payment_id:
            return None

        try:
            resp = requests.get(self._validation_url(), params={
                "val_id": val_id,
                "store_id": settings.SSLCOMMERZ_STORE_ID,
                "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
                "format": "json",
            }, timeout=15)
            resp.raise_for_status()
            validation = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("SSLCommerz validation call failed: %s", exc)
            return None

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return None

        if validation.get("status") not in ("VALID", "VALIDATED"):
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return payment

        payment.status = Payment.Status.SUCCEEDED
        payment.external_reference = validation.get("bank_tran_id", payment.external_reference)
        payment.save(update_fields=["status", "external_reference"])

        if payment.subscription_id:
            sub = payment.subscription
            sub.status = Subscription.Status.ACTIVE
            sub.current_period_start = timezone.now()
            sub.save(update_fields=["status", "current_period_start"])

        return payment
