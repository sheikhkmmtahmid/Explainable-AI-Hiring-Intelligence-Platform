from django.core.management.base import BaseCommand

from apps.billing.models import PaymentProvider, Plan

# Stripe's own "fully supported" country list (stripe.com/global, checked
# 2026-07-08) -- everywhere on this list, Stripe is the sensible
# international default. Bangladesh is deliberately absent: Stripe doesn't
# support it directly, which is exactly why SSLCommerz exists below.
STRIPE_COUNTRIES = [
    "AU", "AT", "BE", "BR", "BG", "CA", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
    "GI", "GR", "HK", "HU", "IE", "IT", "JP", "LV", "LI", "LT", "LU", "MY", "MT", "MX",
    "NL", "NZ", "NO", "PL", "PT", "RO", "SG", "SK", "SI", "ES", "SE", "CH", "TH", "AE",
    "GB", "US",
]

PROVIDERS = [
    {
        "code": "stripe",
        "name": "Card (Stripe)",
        "description": "International cards, Apple Pay, Google Pay. Confirmed automatically via webhook. "
                        "Requires STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET to be configured.",
        "is_automated": True,
        "recommended_countries": STRIPE_COUNTRIES,
    },
    {
        "code": "sslcommerz",
        "name": "bKash / Nagad / Rocket / Card (SSLCommerz)",
        "description": "Bangladesh's leading payment aggregator -- one checkout covers bKash, Nagad, Rocket, "
                        "Dutch-Bangla mobile banking, local/international cards, and net banking. Confirmed "
                        "automatically via IPN webhook. Requires SSLCOMMERZ_STORE_ID / SSLCOMMERZ_STORE_PASSWORD.",
        "is_automated": True,
        "recommended_countries": ["BD"],
    },
    {
        "code": "manual",
        "name": "Bank Transfer / Other",
        "description": "Pay via bank transfer, cash, or any method not listed -- submit a reference/note after "
                        "paying and a platform admin confirms it. Works everywhere, for anything.",
        "is_automated": False,
        "recommended_countries": [],
    },
]

PLANS = [
    {"name": "Starter", "slug": "starter", "price": "0.00", "currency": "USD",
     "max_active_jobs": 3, "max_seats": 3,
     "description": "Try it out: up to 3 active jobs, 3 team seats."},
    {"name": "Growth", "slug": "growth", "price": "99.00", "currency": "USD",
     "max_active_jobs": 25, "max_seats": 15,
     "description": "For growing teams: up to 25 active jobs, 15 team seats, fairness audit reports."},
    {"name": "Scale", "slug": "scale", "price": "299.00", "currency": "USD",
     "max_active_jobs": None, "max_seats": None,
     "description": "Unlimited jobs and seats, priority support."},
]


class Command(BaseCommand):
    help = "Seed payment providers and subscription plans."

    def handle(self, *args, **options):
        created_p = updated_p = 0
        for row in PROVIDERS:
            code = row.pop("code")
            _, created = PaymentProvider.objects.update_or_create(code=code, defaults=row)
            created_p += created
            updated_p += not created

        created_pl = updated_pl = 0
        for row in PLANS:
            slug = row.pop("slug")
            _, created = Plan.objects.update_or_create(slug=slug, defaults=row)
            created_pl += created
            updated_pl += not created

        self.stdout.write(self.style.SUCCESS(
            f"Payment providers: {created_p} created, {updated_p} updated. "
            f"Plans: {created_pl} created, {updated_pl} updated."
        ))
