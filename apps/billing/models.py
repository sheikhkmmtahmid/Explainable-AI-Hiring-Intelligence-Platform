from django.conf import settings
from django.db import models


class Plan(models.Model):
    """A subscription tier, platform-staff managed."""

    class Interval(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    billing_interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTHLY)
    max_active_jobs = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    max_seats = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    is_active = models.BooleanField(default=True, help_text="Offered to new signups")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_plan"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency}/{self.billing_interval})"


class PaymentProvider(models.Model):
    """
    Catalog of payment rails the platform can accept -- seeded via
    `seed_payment_providers` management command, not hand-created per
    organization. Keeping this as data (not a hardcoded enum scattered
    through the codebase) is what makes "any payment method, chosen per
    country" actually open-ended: adding a new rail is a new row plus one
    small provider class, not a rewrite of the billing flow.
    """
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_automated = models.BooleanField(
        default=False,
        help_text="True = confirmed instantly via webhook (Stripe, SSLCommerz). "
                   "False = organization submits proof, platform staff confirms manually.",
    )
    # ISO 3166-1 alpha-2 codes where this is the *recommended* default --
    # empty list means "available everywhere" (this is how manual/bank
    # transfer stays a universal fallback for any country/method not yet
    # automated).
    recommended_countries = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, help_text="Disable if not yet configured (no API keys set).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_payment_provider"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        INCOMPLETE = "incomplete", "Incomplete"  # created, no successful payment yet
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELED = "canceled", "Canceled"

    organization = models.OneToOneField(
        "organizations.Organization", on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INCOMPLETE)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscription"

    def __str__(self):
        return f"{self.organization.name}: {self.plan.name} ({self.status})"

    @property
    def is_usable(self):
        """Whether the org should currently get access -- active/trialing,
        or past_due (grace period; still counts as usable, just flagged for
        the org to fix payment) but not canceled/incomplete."""
        return self.status in (self.Status.ACTIVE, self.Status.TRIALING, self.Status.PAST_DUE)


class OrganizationPaymentMethod(models.Model):
    """How an org intends to pay -- which rail, plus whatever bookkeeping
    that rail needs (Stripe customer ID, or just a human-readable label for
    manual methods)."""
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="payment_methods"
    )
    provider = models.ForeignKey(PaymentProvider, on_delete=models.PROTECT, related_name="org_methods")
    is_default = models.BooleanField(default=True)
    external_customer_id = models.CharField(max_length=255, blank=True)
    external_subscription_id = models.CharField(max_length=255, blank=True)
    manual_label = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_organization_payment_method"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.organization.name} via {self.provider.name}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUBMITTED = "submitted", "Submitted (awaiting review)"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="payments"
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    provider = models.ForeignKey(PaymentProvider, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Automated providers: their transaction/session ID, set by our webhook handler.
    # Manual providers: whatever reference the org typed in (bKash TrxID, bank
    # reference number, etc.) -- free text because "any payment method" means
    # we can't assume a fixed reference format.
    external_reference = models.CharField(max_length=255, blank=True)
    proof_note = models.TextField(blank=True, help_text="Org's description of how/when they paid, for manual review.")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_payments",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization.name}: {self.amount} {self.currency} ({self.status})"
