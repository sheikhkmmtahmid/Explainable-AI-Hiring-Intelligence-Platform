from rest_framework import serializers

from .models import OrganizationPaymentMethod, Payment, PaymentProvider, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id", "name", "slug", "description", "price", "currency", "billing_interval",
            "max_active_jobs", "max_seats", "is_active",
        ]


class PaymentProviderSerializer(serializers.ModelSerializer):
    is_configured = serializers.SerializerMethodField()

    class Meta:
        model = PaymentProvider
        fields = [
            "id", "code", "name", "description", "is_automated",
            "recommended_countries", "is_active", "is_configured",
        ]

    def get_is_configured(self, obj):
        from .providers.registry import get_provider
        try:
            return get_provider(obj.code).is_configured()
        except ValueError:
            return False


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "plan", "status", "current_period_start", "current_period_end",
            "cancel_at_period_end", "created_at",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "organization", "organization_name", "subscription", "provider", "provider_name",
            "amount", "currency", "status", "external_reference", "proof_note",
            "reviewed_by", "reviewed_at", "created_at",
        ]
        read_only_fields = ["id", "organization", "organization_name", "subscription", "provider",
                             "provider_name", "amount", "currency", "status",
                             "reviewed_by", "reviewed_at", "created_at"]


class OrganizationPaymentMethodSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = OrganizationPaymentMethod
        fields = ["id", "provider", "provider_name", "is_default", "manual_label", "created_at"]
        read_only_fields = ["id", "provider_name", "created_at"]
