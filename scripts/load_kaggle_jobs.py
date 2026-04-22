"""
Load Kaggle job posting datasets into JobPost + JobSkillRequirement tables.

Supported dataset formats
--------------------------
Format A — "Job Recommendation Dataset" / generic posting CSV
    Columns: title, company, location, description, requirements, job_type, experience_level

Format B — "Data Science Job Listings" style
    Columns: Job Title, Company Name, Location, Job Description, Industry, Sector

Format C — flat description only
    Columns: job_title, job_description   (minimal)

Usage
-----
    python scripts/load_kaggle_jobs.py --file data/kaggle/jobs.csv --format a --limit 500
    python scripts/load_kaggle_jobs.py --file data/kaggle/jobs.csv --format b --dry-run
"""

import argparse
import csv
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from apps.jobs.models import JobPost, JobSkillRequirement
from apps.parsing.services import extract_skills_from_text

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EXPERIENCE_LEVEL_MAP = {
    "entry": "entry", "junior": "entry", "intern": "entry", "graduate": "entry",
    "mid": "mid", "intermediate": "mid", "associate": "mid",
    "senior": "senior", "sr": "senior", "staff": "senior",
    "lead": "lead", "principal": "lead", "manager": "lead",
    "executive": "executive", "director": "executive", "vp": "executive", "cto": "executive",
}

EMPLOYMENT_TYPE_MAP = {
    "full": "full_time", "full-time": "full_time", "fulltime": "full_time",
    "part": "part_time", "part-time": "part_time", "parttime": "part_time",
    "contract": "contract", "contractor": "contract",
    "intern": "internship", "internship": "internship",
    "freelance": "freelance",
}


def _infer_experience_level(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    for keyword, level in EXPERIENCE_LEVEL_MAP.items():
        if keyword in text:
            return level
    return "mid"


def _infer_employment_type(row: dict) -> str:
    for col in ("job_type", "employment_type", "type", "contract_type"):
        val = (row.get(col) or "").lower().strip()
        if val:
            for keyword, emp_type in EMPLOYMENT_TYPE_MAP.items():
                if keyword in val:
                    return emp_type
    return "full_time"


def _parse_location(location_str: str) -> dict:
    parts = [p.strip() for p in location_str.split(",")]
    return {
        "city": parts[0] if len(parts) >= 1 else "",
        "region": parts[1] if len(parts) >= 2 else "",
        "country": parts[-1] if len(parts) >= 2 else parts[0] if parts else "",
    }


def _extract_salary(text: str) -> tuple:
    pattern = r"\$?([\d,]+)k?\s*[-–to]+\s*\$?([\d,]+)k?"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            low = float(match.group(1).replace(",", ""))
            high = float(match.group(2).replace(",", ""))
            if low < 1000:
                low *= 1000
            if high < 1000:
                high *= 1000
            return low, high
        except (ValueError, AttributeError):
            pass
    return None, None


def _build_external_id(row: dict, index: int) -> str:
    return row.get("id") or row.get("job_id") or f"kaggle_{index}"


def _trunc(value: str, length: int) -> str:
    return (value or "")[:length]


def load_format_a(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format A: title | company | location | description | requirements | job_type | experience_level
    """
    created = skipped = 0
    for i, row in enumerate(reader):
        if limit and created >= limit:
            break

        title = (row.get("title") or row.get("job_title") or "").strip()
        company = (row.get("company") or row.get("company_name") or "Unknown Company").strip()
        description = (row.get("description") or row.get("job_description") or "").strip()

        if not title or not description:
            skipped += 1
            continue

        external_id = _build_external_id(row, i)
        if JobPost.objects.filter(source="kaggle", external_id=external_id).exists():
            skipped += 1
            continue

        location_str = row.get("location") or row.get("job_location") or ""
        loc = _parse_location(location_str)
        requirements = row.get("requirements") or row.get("job_requirements") or ""
        salary_text = description + " " + requirements
        salary_min, salary_max = _extract_salary(salary_text)
        exp_level = (row.get("experience_level") or "").strip().lower() or _infer_experience_level(title, description)
        exp_level = EXPERIENCE_LEVEL_MAP.get(exp_level, "mid")
        industry = (row.get("industry") or row.get("sector") or "").strip()

        skills = extract_skills_from_text(description + " " + requirements)

        if not dry_run:
            job = JobPost.objects.create(
                title=_trunc(title, 300),
                company=_trunc(company, 255),
                description=description,
                requirements=requirements,
                country=_trunc(loc["country"], 200),
                city=_trunc(loc["city"], 200),
                region=_trunc(loc["region"], 200),
                employment_type=_infer_employment_type(row),
                experience_level=exp_level,
                industry=_trunc(industry, 255),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                source="kaggle",
                external_id=_trunc(external_id, 255),
                status="active",
                is_synthetic=False,
            )
            JobSkillRequirement.objects.bulk_create(
                [
                    JobSkillRequirement(
                        job=job,
                        skill_name=s["skill_name"],
                        skill_category=s.get("skill_category", "technical"),
                        is_required=True,
                    )
                    for s in skills
                ],
                ignore_conflicts=True,
            )
        created += 1

        if created % 100 == 0:
            logger.info("Progress: %d jobs loaded", created)

    return created, skipped


def load_format_b(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format B: 'Job Title' | 'Company Name' | 'Location' | 'Job Description' | 'Industry'
    Normalises column names then delegates to format A.
    """
    COL_MAP = {
        "Job Title": "title",
        "Company Name": "company",
        "Location": "location",
        "Job Description": "description",
        "Industry": "industry",
        "Sector": "industry",
        "Job Type": "job_type",
        "Seniority level": "experience_level",
        "Employment type": "job_type",
        "Job function": "job_function",
    }
    normalised_rows = []
    for i, row in enumerate(reader):
        new_row = {COL_MAP.get(k, k.lower().replace(" ", "_")): v for k, v in row.items()}
        if not new_row.get("id") and not new_row.get("job_id"):
            new_row["id"] = f"ds_{i}"
        normalised_rows.append(new_row)

    # Wrap in an iterable that load_format_a can consume
    return load_format_a(iter(normalised_rows), limit, dry_run)


def load_format_c(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format C: minimal — job_title | job_description
    """
    created = skipped = 0
    for i, row in enumerate(reader):
        if limit and created >= limit:
            break

        title = (
            row.get("job_title") or row.get("title") or row.get("position") or ""
        ).strip()
        description = (
            row.get("job_description") or row.get("description") or row.get("text") or ""
        ).strip()

        if not title or not description:
            skipped += 1
            continue

        external_id = _build_external_id(row, i)
        if JobPost.objects.filter(source="kaggle", external_id=external_id).exists():
            skipped += 1
            continue

        skills = extract_skills_from_text(description)

        if not dry_run:
            job = JobPost.objects.create(
                title=_trunc(title, 300),
                company=_trunc(row.get("company", "Unknown Company"), 255),
                description=description,
                employment_type="full_time",
                experience_level=_infer_experience_level(title, description),
                source="kaggle",
                external_id=_trunc(external_id, 255),
                status="active",
                is_synthetic=False,
            )
            JobSkillRequirement.objects.bulk_create(
                [
                    JobSkillRequirement(job=job, skill_name=s["skill_name"], is_required=True)
                    for s in skills
                ],
                ignore_conflicts=True,
            )
        created += 1

        if created % 100 == 0:
            logger.info("Progress: %d jobs loaded", created)

    return created, skipped


LOADERS = {"a": load_format_a, "b": load_format_b, "c": load_format_c}


def main():
    parser = argparse.ArgumentParser(description="Load Kaggle job CSV into HiringAI database")
    parser.add_argument("--file", required=True, help="Path to the Kaggle jobs CSV file")
    parser.add_argument(
        "--format",
        choices=list(LOADERS.keys()),
        default="a",
        help="Dataset format (default: a — generic job posting)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max jobs to load (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Parse without writing to DB")
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.exists():
        logger.error("File not found: %s", csv_path)
        sys.exit(1)

    with open(csv_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        created, skipped = LOADERS[args.format](reader, args.limit, args.dry_run)

    mode = "[DRY RUN] " if args.dry_run else ""
    logger.info("%sFinished. Created: %d  |  Skipped: %d", mode, created, skipped)


if __name__ == "__main__":
    main()
