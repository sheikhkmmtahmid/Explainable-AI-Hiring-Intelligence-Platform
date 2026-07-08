class PaymentProviderBase:
    """
    Common interface every payment rail implements. The billing views only
    ever talk to this interface -- adding a new payment method later means
    writing one small class here plus a PaymentProvider row, not touching
    the checkout/webhook views at all.
    """
    code: str = ""

    def is_configured(self) -> bool:
        """Whether the platform operator has actually set this provider's
        API keys yet. Lets the frontend hide/disable a rail that exists in
        the catalog but isn't live, instead of crashing on checkout."""
        raise NotImplementedError

    def start_checkout(self, *, organization, plan, payment) -> dict:
        """
        Kick off payment for `payment` (a Payment row already created in
        PENDING status). Returns a dict the frontend can act on:
          - automated providers: {"redirect_url": "https://..."}
          - manual provider: {"instructions": "...", "requires_proof": True}
        """
        raise NotImplementedError
