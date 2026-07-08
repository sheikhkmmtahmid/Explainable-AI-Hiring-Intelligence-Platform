from django.db import models


class Organization(models.Model):
    """
    A paying customer -- one HR company/agency. This is the tenancy
    boundary: every JobPost belongs to exactly one Organization, and
    everything downstream (Applications, MatchResults, fairness reports,
    candidates sourced privately) is only ever visible within that
    boundary. Candidates themselves stay organization-agnostic (a person
    isn't owned by a company) -- visibility into a candidate is granted by
    an Application to one of the org's jobs, or by the org having sourced
    them directly (see Candidate.sourced_by_organization).
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    country = models.CharField(
        max_length=2, blank=True,
        help_text="ISO 3166-1 alpha-2 (e.g. BD, US, GB) -- used to pick sensible default payment methods.",
    )
    industry = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations_organization"
        ordering = ["name"]

    def __str__(self):
        return self.name
