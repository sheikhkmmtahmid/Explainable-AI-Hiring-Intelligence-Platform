import logging
from django.utils import timezone
from config.celery import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def ingest_adzuna_jobs_task(self, query: str, country: str = "gb", location: str = "", pages: int = 2):
    from apps.ingestion.models import IngestionRun
    from apps.ingestion.services import ingest_from_adzuna, save_jobs_from_raw

    run = IngestionRun.objects.create(
        source=IngestionRun.Source.ADZUNA,
        query=query,
        location=location,
        country_code=country,
        status=IngestionRun.Status.RUNNING,
        started_at=timezone.now(),
    )
    total_fetched = total_created = total_skipped = 0
    try:
        for page in range(1, pages + 1):
            raw = ingest_from_adzuna(query, country, location, page)
            total_fetched += len(raw)
            created, skipped = save_jobs_from_raw(raw, "adzuna")
            total_created += created
            total_skipped += skipped

        run.status = IngestionRun.Status.DONE
        run.jobs_fetched = total_fetched
        run.jobs_created = total_created
        run.jobs_skipped = total_skipped
        run.completed_at = timezone.now()
        run.save()
        logger.info("Adzuna ingestion done: fetched=%s created=%s", total_fetched, total_created)
    except Exception as exc:
        run.status = IngestionRun.Status.FAILED
        run.error_message = str(exc)
        run.save()
        logger.error("Adzuna ingestion failed: %s", exc)
        raise
