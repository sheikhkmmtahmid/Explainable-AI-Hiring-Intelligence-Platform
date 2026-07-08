from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        RECRUITER = "recruiter", "Recruiter"
        CANDIDATE = "candidate", "Candidate"
        ANALYST = "analyst", "Analyst"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)
    # Which company this account belongs to -- the tenancy boundary. Null for
    # candidates (a person isn't owned by one company) and for platform staff
    # (is_superuser=True), who manage the whole system rather than one tenant.
    organization = models.ForeignKey(
        "organizations.Organization", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="members",
        # db_constraint=False: this TiDB instance fails when a migration's
        # AddField combines "ADD COLUMN" + "ADD FOREIGN KEY" into one ALTER
        # TABLE statement (reproduced multiple times this session). Django
        # still enforces the relationship at the ORM level; only the DB-level
        # constraint is skipped. See project memory for full details.
        db_constraint=False,
    )
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    @property
    def is_candidate_user(self):
        return self.role == self.Role.CANDIDATE

    @property
    def is_platform_staff(self):
        """Runs the platform itself (support/billing across all customers),
        as opposed to an org admin who only manages their own company's
        account. Distinct from Role.ADMIN -- see that role's docstring-ish
        comment on `organization` above."""
        return self.is_superuser
