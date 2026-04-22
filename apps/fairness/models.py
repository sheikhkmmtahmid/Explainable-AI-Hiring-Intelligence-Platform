from django.db import models


class FairnessReport(models.Model):
    job = models.ForeignKey(
        "jobs.JobPost", on_delete=models.CASCADE, related_name="fairness_reports"
    )
    protected_attribute = models.CharField(max_length=50)  # e.g. gender, ethnicity, age_range
    report_data = models.JSONField(default=dict)
    disparate_impact_ratio = models.FloatField(null=True, blank=True)
    selection_rate_overall = models.FloatField(null=True, blank=True)
    bias_flag = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fairness_report"
        unique_together = [["job", "protected_attribute"]]
        ordering = ["-generated_at"]

    def __str__(self):
        return f"FairnessReport: {self.job.title} [{self.protected_attribute}]"


class SubgroupMetric(models.Model):
    report = models.ForeignKey(FairnessReport, on_delete=models.CASCADE, related_name="subgroups")
    group_value = models.CharField(max_length=100)
    total_candidates = models.IntegerField(default=0)
    shortlisted_count = models.IntegerField(default=0)
    selection_rate = models.FloatField(default=0.0)
    avg_match_score = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "fairness_subgroup"
        unique_together = [["report", "group_value"]]

    def __str__(self):
        return f"{self.report.protected_attribute}={self.group_value}: {self.selection_rate:.1%}"
