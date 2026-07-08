from django.contrib import admin

from .models import OrganizationPaymentMethod, Payment, PaymentProvider, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "currency", "billing_interval", "max_active_jobs", "max_seats", "is_active"]
    list_filter = ["is_active", "billing_interval"]


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_automated", "is_active"]
    list_filter = ["is_automated", "is_active"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["organization", "plan", "status", "current_period_end"]
    list_filter = ["status", "plan"]
    search_fields = ["organization__name"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["organization", "amount", "currency", "provider", "status", "created_at"]
    list_filter = ["status", "provider"]
    search_fields = ["organization__name", "external_reference"]

    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected payments (activates subscription)")
    def approve_selected(self, request, queryset):
        from django.utils import timezone
        from .models import Subscription

        count = 0
        for payment in queryset.filter(status=Payment.Status.SUBMITTED):
            payment.status = Payment.Status.SUCCEEDED
            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            if payment.subscription_id:
                sub = payment.subscription
                sub.status = Subscription.Status.ACTIVE
                sub.current_period_start = timezone.now()
                sub.save(update_fields=["status", "current_period_start"])
            count += 1
        self.message_user(request, f"Approved {count} payment(s).")

    @admin.action(description="Reject selected payments")
    def reject_selected(self, request, queryset):
        from django.utils import timezone

        count = queryset.filter(status=Payment.Status.SUBMITTED).update(
            status=Payment.Status.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"Rejected {count} payment(s).")


@admin.register(OrganizationPaymentMethod)
class OrganizationPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["organization", "provider", "is_default", "created_at"]
    list_filter = ["provider"]
