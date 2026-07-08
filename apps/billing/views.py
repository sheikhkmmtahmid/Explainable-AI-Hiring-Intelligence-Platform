import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, PaymentProvider, Plan, Subscription
from .providers.registry import get_provider
from .serializers import PaymentSerializer, PaymentProviderSerializer, PlanSerializer, SubscriptionSerializer

logger = logging.getLogger(__name__)


def _require_org_admin(user):
    """Only an org's own admin (or platform staff, for support) manages
    that org's billing -- a recruiter shouldn't be able to change what the
    company is paying for."""
    if user.is_platform_staff:
        return
    if user.role != "admin" or not user.organization_id:
        raise PermissionDenied("Only your organization's admin can manage billing.")


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentProviderListView(generics.ListAPIView):
    """Providers this organization can pick from, active ones only. The
    frontend uses `recommended_countries` + the org's own country to
    highlight the sensible default (e.g. SSLCommerz for a Bangladeshi
    org) without hiding the others -- it's still the org's choice."""
    serializer_class = PaymentProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentProvider.objects.filter(is_active=True)


class SubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.organization_id:
            return Response({"detail": "Not linked to an organization."}, status=status.HTTP_404_NOT_FOUND)
        sub = Subscription.objects.filter(organization_id=user.organization_id).select_related("plan").first()
        if not sub:
            return Response(None)
        return Response(SubscriptionSerializer(sub).data)


class SubscribeView(APIView):
    """Start (or switch) a subscription: creates/updates the Subscription
    row plus a Payment, and asks the chosen provider to begin checkout."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        _require_org_admin(user)
        organization = user.organization

        plan = get_object_or_404(Plan, id=request.data.get("plan_id"), is_active=True)
        provider_row = get_object_or_404(PaymentProvider, code=request.data.get("provider_code"), is_active=True)
        provider = get_provider(provider_row.code)
        if not provider.is_configured():
            return Response(
                {"detail": f"{provider_row.name} isn't set up yet -- ask the platform operator to add API keys."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription, _ = Subscription.objects.update_or_create(
            organization=organization,
            defaults={"plan": plan, "status": Subscription.Status.INCOMPLETE},
        )
        payment = Payment.objects.create(
            organization=organization, subscription=subscription, provider=provider_row,
            amount=plan.price, currency=plan.currency, status=Payment.Status.PENDING,
        )

        try:
            result = provider.start_checkout(organization=organization, plan=plan, payment=payment)
        except RuntimeError as exc:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"payment_id": payment.id, **result}, status=status.HTTP_201_CREATED)


class SubmitPaymentProofView(APIView):
    """For the manual provider: the org tells us how/when they paid."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        user = request.user
        _require_org_admin(user)
        payment = get_object_or_404(Payment, id=payment_id, organization_id=user.organization_id)
        if payment.status not in (Payment.Status.PENDING, Payment.Status.REJECTED):
            return Response({"detail": f"Payment is already {payment.status}."}, status=status.HTTP_400_BAD_REQUEST)

        payment.proof_note = request.data.get("proof_note", "")
        payment.external_reference = request.data.get("external_reference", "")
        payment.status = Payment.Status.SUBMITTED
        payment.save(update_fields=["proof_note", "external_reference", "status"])
        return Response(PaymentSerializer(payment).data)


class PendingPaymentReviewListView(generics.ListAPIView):
    """Platform-staff moderation queue for manual payments."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_platform_staff:
            return Payment.objects.none()
        return Payment.objects.filter(status=Payment.Status.SUBMITTED).select_related("organization", "provider")

    def list(self, request, *args, **kwargs):
        if not request.user.is_platform_staff:
            return Response({"detail": "Platform staff only."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)


class ReviewPaymentView(APIView):
    """POST {"action": "approve"|"reject"} -- platform staff confirms or
    rejects a manually-submitted payment."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        if not request.user.is_platform_staff:
            return Response({"detail": "Platform staff only."}, status=status.HTTP_403_FORBIDDEN)

        payment = get_object_or_404(Payment, id=payment_id)
        if payment.status != Payment.Status.SUBMITTED:
            return Response({"detail": f"Payment is {payment.status}, not awaiting review."}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get("action")
        payment.reviewed_by = request.user
        payment.reviewed_at = timezone.now()

        if action == "approve":
            payment.status = Payment.Status.SUCCEEDED
            payment.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            if payment.subscription_id:
                sub = payment.subscription
                sub.status = Subscription.Status.ACTIVE
                sub.current_period_start = timezone.now()
                sub.save(update_fields=["status", "current_period_start"])
        elif action == "reject":
            payment.status = Payment.Status.REJECTED
            payment.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        else:
            return Response({"detail": "action must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PaymentSerializer(payment).data)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """Public endpoint -- Stripe calls this directly, no user session.
    Authenticity is verified via the signed payload inside the provider,
    not by DRF auth."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        provider = get_provider("stripe")
        payment = provider.handle_webhook(request)
        if payment is None:
            return Response(status=status.HTTP_200_OK)  # ack anyway; nothing actionable
        return Response(status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class SSLCommerzWebhookView(APIView):
    """Public IPN endpoint -- SSLCommerz posts form-encoded data here."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        provider = get_provider("sslcommerz")
        provider.handle_ipn(request.POST.dict())
        return Response(status=status.HTTP_200_OK)
