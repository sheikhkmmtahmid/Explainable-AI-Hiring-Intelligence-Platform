from django.urls import path

from .views import (
    PaymentProviderListView,
    PendingPaymentReviewListView,
    PlanListView,
    ReviewPaymentView,
    SSLCommerzWebhookView,
    StripeWebhookView,
    SubmitPaymentProofView,
    SubscribeView,
    SubscriptionView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("providers/", PaymentProviderListView.as_view(), name="billing-providers"),
    path("subscription/", SubscriptionView.as_view(), name="billing-subscription"),
    path("subscribe/", SubscribeView.as_view(), name="billing-subscribe"),
    path("payments/<int:payment_id>/submit-proof/", SubmitPaymentProofView.as_view(), name="billing-submit-proof"),
    path("payments/pending-review/", PendingPaymentReviewListView.as_view(), name="billing-pending-review"),
    path("payments/<int:payment_id>/review/", ReviewPaymentView.as_view(), name="billing-review-payment"),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="billing-webhook-stripe"),
    path("webhooks/sslcommerz/", SSLCommerzWebhookView.as_view(), name="billing-webhook-sslcommerz"),
]
