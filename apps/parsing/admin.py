from django.contrib import admin
from .models import ParseJob


@admin.register(ParseJob)
class ParseJobAdmin(admin.ModelAdmin):
    list_display = ["cv", "status", "started_at", "completed_at"]
    list_filter = ["status"]
