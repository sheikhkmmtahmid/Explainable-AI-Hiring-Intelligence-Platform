from django.db import migrations


def reschedule(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    # timezone="Europe/London" makes Celery Beat interpret hour=1 as 1am
    # British time year-round, correctly shifting for BST/GMT -- a plain
    # UTC hour would drift by an hour for half the year.
    daily_1am_london, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="1", day_of_week="*", day_of_month="*", month_of_year="*",
        timezone="Europe/London",
    )
    weekly_monday_1am_london, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="1", day_of_week="1", day_of_month="*", month_of_year="*",
        timezone="Europe/London",
    )

    PeriodicTask.objects.filter(name="Sync ESCO skills").update(crontab=daily_1am_london)
    PeriodicTask.objects.filter(name="Mine corpus skills").update(crontab=weekly_monday_1am_london)


def revert(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    daily_utc, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="3", day_of_week="*", day_of_month="*", month_of_year="*",
    )
    weekly_utc, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="4", day_of_week="1", day_of_month="*", month_of_year="*",
    )
    PeriodicTask.objects.filter(name="Sync ESCO skills").update(crontab=daily_utc)
    PeriodicTask.objects.filter(name="Mine corpus skills").update(crontab=weekly_utc)


class Migration(migrations.Migration):

    dependencies = [
        ("taxonomy", "0003_schedule_skill_discovery_tasks"),
    ]

    operations = [
        migrations.RunPython(reschedule, revert),
    ]
