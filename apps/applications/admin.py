from django.contrib import admin

from .models import Application, ApplicationNote, InterviewSlot


class NoteInline(admin.TabularInline):
    model = ApplicationNote
    extra = 0


class InterviewInline(admin.TabularInline):
    model = InterviewSlot
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "candidate", "job", "status", "overall_match_score", "rank", "applied_at", "is_synthetic"
    ]
    list_filter = ["status", "is_synthetic"]
    search_fields = ["candidate__full_name", "job__title"]
    inlines = [NoteInline, InterviewInline]
