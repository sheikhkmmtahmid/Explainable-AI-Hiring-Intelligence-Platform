from .base import PaymentProviderBase


class ManualProvider(PaymentProviderBase):
    """
    The universal fallback: works in any country, for any payment method
    the platform hasn't automated yet (a direct bank transfer, cash, a
    mobile banking service without a merchant API, etc.). The organization
    pays however they've agreed with the platform operator, then submits a
    reference/note; a platform admin reviews and confirms it. No new code
    is ever needed to support "one more payment method" this way -- it's
    always available, it just isn't instant.
    """
    code = "manual"

    def is_configured(self) -> bool:
        return True  # always available, no API keys involved

    def start_checkout(self, *, organization, plan, payment) -> dict:
        return {
            "requires_proof": True,
            "instructions": (
                f"Pay {payment.amount} {payment.currency} using your agreed method "
                "(bank transfer, cash, or other), then submit the payment reference "
                "below so it can be reviewed and your subscription activated."
            ),
        }
