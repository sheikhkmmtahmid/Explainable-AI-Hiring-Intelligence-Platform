from django.contrib import admin
from django.db.models import OuterRef, Subquery

from .models import Application, ApplicationNote, ApplicationStatusHistory, InterviewSlot


class NoteInline(admin.TabularInline):
    model = ApplicationNote
    extra = 0


class InterviewInline(admin.TabularInline):
    model = InterviewSlot
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "changed_at"]
    can_delete = False
    ordering = ["-changed_at"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "candidate", "job", "status", "match_score", "match_rank", "applied_at", "is_synthetic"
    ]
    list_filter = ["status", "is_synthetic"]
    search_fields = ["candidate__full_name", "job__title"]
    inlines = [StatusHistoryInline, NoteInline, InterviewInline]

    def get_queryset(self, request):
        from apps.matching.models import MatchResult

        qs = super().get_queryset(request)
        match_qs = MatchResult.objects.filter(
            candidate_id=OuterRef("candidate_id"), job_id=OuterRef("job_id")
        )
        return qs.annotate(
            _match_score=Subquery(match_qs.values("overall_score")[:1]),
            _match_rank=Subquery(match_qs.values("rank")[:1]),
        )

    @admin.display(description="Match score", ordering="_match_score")
    def match_score(self, obj):
        return f"{obj._match_score:.0%}" if obj._match_score is not None else "—"

    @admin.display(description="Rank", ordering="_match_rank")
    def match_rank(self, obj):
        return obj._match_rank if obj._match_rank is not None else "—"
