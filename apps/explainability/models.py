from django.db import models


class ExplanationReport(models.Model):
    class Method(models.TextChoices):
        SHAP = "shap", "SHAP"
        LIME = "lime", "LIME"
        COMBINED = "combined", "Combined"

    match_result = models.OneToOneField(
        "matching.MatchResult", on_delete=models.CASCADE, related_name="explanation"
    )
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.COMBINED)

    # SHAP/LIME outputs stored as JSON
    feature_importances = models.JSONField(default=dict)
    top_positive_factors = models.JSONField(default=list)
    top_negative_factors = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    matching_skills = models.JSONField(default=list)
    summary_text = models.TextField(blank=True)

    generated_at = models.DateTimeField(auto_now=True)
    model_version = models.CharField(max_length=50, default="v1")

    class Meta:
        db_table = "explainability_report"

    def __str__(self):
        return f"Explanation [{self.method}]: {self.match_result}"
