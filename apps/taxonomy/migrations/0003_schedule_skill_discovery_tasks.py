from django.db import migrations


def create_periodic_tasks(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    daily, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="3", day_of_week="*", day_of_month="*", month_of_year="*",
    )
    weekly, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="4", day_of_week="1", day_of_month="*", month_of_year="*",
    )

    PeriodicTask.objects.get_or_create(
        name="Sync ESCO skills",
        defaults={
            "task": "apps.taxonomy.tasks.sync_esco_skills_task",
            "crontab": daily,
            "enabled": True,
        },
    )
    PeriodicTask.objects.get_or_create(
        name="Mine corpus skills",
        defaults={
            "task": "apps.taxonomy.tasks.mine_corpus_skills_task",
            "crontab": weekly,
            "enabled": True,
        },
    )


def remove_periodic_tasks(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(
        name__in=["Sync ESCO skills", "Mine corpus skills"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("taxonomy", "0002_pendingskill"),
        ("django_celery_beat", "__first__"),
    ]

    operations = [
        migrations.RunPython(create_periodic_tasks, remove_periodic_tasks),
    ]
