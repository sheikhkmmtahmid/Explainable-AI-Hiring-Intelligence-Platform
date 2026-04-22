from django.contrib import admin
from .models import SyntheticGenerationRun


@admin.register(SyntheticGenerationRun)
class SyntheticGenerationRunAdmin(admin.ModelAdmin):
    list_display = ["kind", "status", "count_requested", "count_created", "created_at"]
    list_filter = ["kind", "status"]
