from django.db import migrations


def backfill(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    JobPost = apps.get_model("jobs", "JobPost")

    default_org, _ = Organization.objects.get_or_create(
        slug="demo-company",
        defaults={"name": "Demo Company", "country": "", "is_active": True},
    )
    JobPost.objects.filter(organization__isnull=True).update(organization=default_org)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_jobpost_organization"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
