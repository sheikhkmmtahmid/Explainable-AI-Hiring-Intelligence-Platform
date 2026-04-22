"""
Load Kaggle resume datasets into the Candidate + CandidateSkill tables.

Supported dataset formats
--------------------------
Format A — "Resume Dataset" by gauravduttakiit (most common)
    Columns: ID, Resume_str, Resume_html, Category
    Download: https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset

Format B — "UpdatedResumedataset" / flat CSV
    Columns: Resume, Category   (or just a text column)

Format C — generic with explicit columns
    Columns: name, email, skills, experience, education, ...

Usage
-----
    # Activate venv first
    python scripts/load_kaggle_resumes.py --file data/kaggle/resume.csv --format a --limit 1000

    # Dry run (no DB writes)
    python scripts/load_kaggle_resumes.py --file data/kaggle/resume.csv --format a --dry-run
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

# Bootstrap Django before any app imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from apps.candidates.models import Candidate, CandidateSkill
from apps.parsing.services import extract_skills_from_text, extract_years_of_experience

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Mapping from Kaggle category labels to our seniority / education fields
CATEGORY_TO_FIELD = {
    "Data Science": "Computer Science",
    "HR": "Human Resources",
    "Advocate": "Law",
    "Arts": "Arts",
    "Web Designing": "Computer Science",
    "Mechanical Engineer": "Engineering",
    "Sales": "Business",
    "Health and fitness": "Medicine",
    "Civil Engineer": "Engineering",
    "Java Developer": "Computer Science",
    "Business Analyst": "Business",
    "SAP Developer": "Computer Science",
    "Automation Testing": "Computer Science",
    "Electrical Engineering": "Engineering",
    "Operations Manager": "Business",
    "Python Developer": "Computer Science",
    "DevOps Engineer": "Computer Science",
    "Network Security Engineer": "Computer Science",
    "PMO": "Business",
    "Database": "Computer Science",
    "Hadoop": "Computer Science",
    "ETL Developer": "Computer Science",
    "DotNet Developer": "Computer Science",
    "Blockchain": "Computer Science",
    "Testing": "Computer Science",
}


def _safe_email(index: int) -> str:
    return f"kaggle_candidate_{index}@synthetic.hiringai.local"


def load_format_a(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format A: columns = ID | Resume_str | Resume_html | Category
    """
    created = skipped = 0
    for i, row in enumerate(reader):
        if limit and created >= limit:
            break

        raw_text = (row.get("Resume_str") or row.get("Resume") or "").strip()
        category = (row.get("Category") or "").strip()
        if not raw_text:
            skipped += 1
            continue

        email = _safe_email(i)
        if Candidate.objects.filter(email=email).exists():
            skipped += 1
            continue

        skills = extract_skills_from_text(raw_text)
        years_exp = extract_years_of_experience(raw_text)
        edu_field = CATEGORY_TO_FIELD.get(category, "Other")

        if not dry_run:
            candidate = Candidate.objects.create(
                full_name=f"Kaggle Candidate {i}",
                email=email,
                current_title=category,
                years_of_experience=years_exp,
                education_field=edu_field,
                raw_cv_text=raw_text,
                is_synthetic=True,
                summary=raw_text[:500],
            )
            CandidateSkill.objects.bulk_create(
                [
                    CandidateSkill(
                        candidate=candidate,
                        skill_name=s["skill_name"],
                        skill_category=s.get("skill_category", "technical"),
                        source="cv_parsed",
                    )
                    for s in skills
                ],
                ignore_conflicts=True,
            )
        created += 1

        if created % 100 == 0:
            logger.info("Progress: %d candidates loaded", created)

    return created, skipped


def load_format_b(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format B: columns = Resume | Category  (UpdatedResumedataset style)
    Falls back to same logic as A.
    """
    # Remap column names to match format A
    for row in reader:
        if "Resume" in row and "Resume_str" not in row:
            row["Resume_str"] = row.pop("Resume")
    return load_format_a(reader, limit, dry_run)


def load_format_generic(reader: csv.DictReader, limit: int, dry_run: bool) -> tuple[int, int]:
    """
    Format C: tries to extract from any column named 'text', 'resume', 'cv', 'content'.
    """
    TEXT_COLS = ["text", "resume", "cv", "content", "resume_text", "cv_text", "description"]
    created = skipped = 0

    for i, row in enumerate(reader):
        if limit and created >= limit:
            break

        raw_text = ""
        for col in TEXT_COLS:
            val = row.get(col) or row.get(col.upper()) or row.get(col.capitalize()) or ""
            if val.strip():
                raw_text = val.strip()
                break

        if not raw_text:
            skipped += 1
            continue

        email = _safe_email(i)
        if Candidate.objects.filter(email=email).exists():
            skipped += 1
            continue

        skills = extract_skills_from_text(raw_text)
        years_exp = extract_years_of_experience(raw_text)

        if not dry_run:
            candidate = Candidate.objects.create(
                full_name=f"Kaggle Candidate {i}",
                email=email,
                years_of_experience=years_exp,
                raw_cv_text=raw_text,
                is_synthetic=True,
                summary=raw_text[:500],
            )
            CandidateSkill.objects.bulk_create(
                [
                    CandidateSkill(
                        candidate=candidate,
                        skill_name=s["skill_name"],
                        skill_category=s.get("skill_category", "technical"),
                        source="cv_parsed",
                    )
                    for s in skills
                ],
                ignore_conflicts=True,
            )
        created += 1

        if created % 100 == 0:
            logger.info("Progress: %d candidates loaded", created)

    return created, skipped


LOADERS = {
    "a": load_format_a,
    "b": load_format_b,
    "generic": load_format_generic,
}


def main():
    parser = argparse.ArgumentParser(description="Load Kaggle resume CSV into HiringAI database")
    parser.add_argument("--file", required=True, help="Path to the Kaggle CSV file")
    parser.add_argument(
        "--format",
        choices=list(LOADERS.keys()),
        default="a",
        help="Dataset format (default: a — gauravduttakiit/resume-dataset)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max candidates to load (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Parse without writing to DB")
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.exists():
        logger.error("File not found: %s", csv_path)
        sys.exit(1)

    loader_fn = LOADERS[args.format]

    with open(csv_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        created, skipped = loader_fn(reader, args.limit, args.dry_run)

    mode = "[DRY RUN] " if args.dry_run else ""
    logger.info("%sFinished. Created: %d  |  Skipped: %d", mode, created, skipped)


if __name__ == "__main__":
    main()
