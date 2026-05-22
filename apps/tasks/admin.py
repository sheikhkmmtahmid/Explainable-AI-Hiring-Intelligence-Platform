from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "created_by", "assigned_to", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "description"]
