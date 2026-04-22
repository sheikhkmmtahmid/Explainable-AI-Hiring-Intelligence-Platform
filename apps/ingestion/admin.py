from django.contrib import admin
from .models import IngestionRun


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ["source", "status", "query", "jobs_fetched", "jobs_created", "created_at"]
    list_filter = ["source", "status"]
