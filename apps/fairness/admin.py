from django.contrib import admin
from .models import FairnessReport, SubgroupMetric


class SubgroupInline(admin.TabularInline):
    model = SubgroupMetric
    extra = 0


@admin.register(FairnessReport)
class FairnessReportAdmin(admin.ModelAdmin):
    list_display = ["job", "protected_attribute", "disparate_impact_ratio", "bias_flag", "generated_at"]
    list_filter = ["protected_attribute", "bias_flag"]
    inlines = [SubgroupInline]
