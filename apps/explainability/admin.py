from django.contrib import admin
from .models import ExplanationReport


@admin.register(ExplanationReport)
class ExplanationReportAdmin(admin.ModelAdmin):
    list_display = ["match_result", "method", "generated_at"]
    list_filter = ["method"]
