"""
Job data ingestion from external APIs (Adzuna, Jooble, The Muse).
Never scrapes LinkedIn/Indeed.
"""
import logging
from typing import Optional

import requests
from django.conf import settings

from apps.jobs.models import JobPost

logger = logging.getLogger(__name__)


def ingest_from_adzuna(
    query: str,
    country: str = "gb",
    location: str = "",
    page: int = 1,
    results_per_page: int = 50,
) -> list[dict]:
    """Fetch jobs from Adzuna API."""
    app_id = settings.ADZUNA_APP_ID
    api_key = settings.ADZUNA_API_KEY
    if not app_id or not api_key:
        logger.warning("Adzuna credentials not configured")
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": api_key,
        "results_per_page": results_per_page,
        "what": query,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except requests.RequestException as e:
        logger.error("Adzuna API error: %s", e)
        return []


def normalise_adzuna_job(raw: dict) -> Optional[dict]:
    """Map Adzuna API response to our JobPost fields."""
    if not raw.get("title") or not raw.get("company", {}).get("display_name"):
        return None
    return {
        "title": raw["title"],
        "company": raw["company"]["display_name"],
        "description": raw.get("description", ""),
        "country": raw.get("location", {}).get("area", [""])[0],
        "city": raw.get("location", {}).get("display_name", ""),
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "external_url": raw.get("redirect_url", ""),
        "external_id": raw.get("id", ""),
        "source": "adzuna",
    }


def save_jobs_from_raw(raw_jobs: list[dict], source: str) -> tuple[int, int]:
    """Persist normalised job dicts. Returns (created, skipped) counts."""
    created = skipped = 0
    for raw in raw_jobs:
        if source == "adzuna":
            data = normalise_adzuna_job(raw)
        else:
            data = raw  # Already normalised upstream

        if not data:
            skipped += 1
            continue

        _, was_created = JobPost.objects.get_or_create(
            source=source,
            external_id=data.get("external_id", ""),
            defaults={**data, "is_synthetic": False},
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    return created, skipped
