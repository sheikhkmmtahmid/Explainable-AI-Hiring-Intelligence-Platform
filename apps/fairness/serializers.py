from rest_framework import serializers
from .models import FairnessReport, SubgroupMetric


class SubgroupMetricSerializer(serializers.ModelSerializer):
    # Frontend-friendly aliases
    total_count    = serializers.IntegerField(source="total_candidates")
    selected_count = serializers.IntegerField(source="shortlisted_count")
    disparate_impact = serializers.SerializerMethodField()

    class Meta:
        model = SubgroupMetric
        fields = [
            "group_value",
            "total_count", "selected_count",
            "selection_rate", "avg_match_score",
            "disparate_impact",
        ]

    def get_disparate_impact(self, obj):
        # DI = this group's selection rate / max selection rate across all groups in this report
        siblings = obj.report.subgroups.all()
        rates = [s.selection_rate for s in siblings if s.selection_rate is not None]
        max_rate = max(rates) if rates else 0
        if max_rate == 0:
            return None
        return round(float(obj.selection_rate) / max_rate, 4)


class FairnessReportSerializer(serializers.ModelSerializer):
    subgroups = SubgroupMetricSerializer(many=True, read_only=True)
    # Frontend-friendly aliases
    disparate_impact         = serializers.FloatField(source="disparate_impact_ratio", allow_null=True)
    bias_detected            = serializers.BooleanField(source="bias_flag")
    demographic_parity_difference = serializers.SerializerMethodField()

    class Meta:
        model = FairnessReport
        fields = [
            "id", "job", "protected_attribute",
            "disparate_impact", "disparate_impact_ratio",
            "selection_rate_overall", "bias_flag", "bias_detected",
            "demographic_parity_difference",
            "subgroups", "generated_at",
        ]
        read_only_fields = fields

    def get_demographic_parity_difference(self, obj):
        rates = [s.selection_rate for s in obj.subgroups.all()]
        if len(rates) < 2:
            return 0.0
        return round(float(max(rates)) - float(min(rates)), 4)
