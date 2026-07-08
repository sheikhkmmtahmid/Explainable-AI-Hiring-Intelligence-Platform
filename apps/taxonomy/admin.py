from django.contrib import admin
from .models import SkillTaxonomy, JobRoleTemplate, PendingSkill


@admin.register(SkillTaxonomy)
class SkillTaxonomyAdmin(admin.ModelAdmin):
    list_display = ["canonical_name", "category", "subcategory", "is_technical"]
    list_filter = ["category", "is_technical"]
    search_fields = ["name", "canonical_name"]


@admin.register(JobRoleTemplate)
class JobRoleTemplateAdmin(admin.ModelAdmin):
    list_display = ["title", "industry", "typical_experience_years"]
    search_fields = ["title", "industry"]
    filter_horizontal = ["core_skills"]


@admin.register(PendingSkill)
class PendingSkillAdmin(admin.ModelAdmin):
    list_display = [
        "proposed_name", "status", "source", "similar_existing_skill",
        "similarity_match_type", "similarity_score", "created_at",
    ]
    list_filter = ["status", "source", "similarity_match_type"]
    search_fields = ["proposed_name"]
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected pending skills")
    def approve_selected(self, request, queryset):
        from .services import approve_pending_skill

        count = 0
        for pending in queryset.filter(status=PendingSkill.Status.PENDING):
            approve_pending_skill(pending, reviewer=request.user)
            count += 1
        self.message_user(request, f"Approved {count} skill(s).")

    @admin.action(description="Reject selected pending skills")
    def reject_selected(self, request, queryset):
        from .services import reject_pending_skill

        count = 0
        for pending in queryset.filter(status=PendingSkill.Status.PENDING):
            reject_pending_skill(pending, reviewer=request.user)
            count += 1
        self.message_user(request, f"Rejected {count} skill(s).")
