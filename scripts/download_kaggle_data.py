"""
Download all required Kaggle datasets into data/kaggle/.

Datasets downloaded
-------------------
Resumes:
  gauravduttakiit/resume-dataset          → data/kaggle/resumes/resume.csv
  snehaanbhawal/resume-dataset            → data/kaggle/resumes/UpdatedResumeDataSet.csv

Jobs:
  PromptCloudHQ/us-jobs-on-monstercom     → data/kaggle/jobs/monster_com-job_sample.csv
  andrewmvd/data-scientist-jobs           → data/kaggle/jobs/DataScientist.csv
  shivamb/real-or-fake-fake-jobpostings   → data/kaggle/jobs/fake_job_postings.csv

Prerequisites
-------------
1. Create a free account at https://www.kaggle.com
2. Go to https://www.kaggle.com/settings  → API section → "Create New Token"
3. This downloads kaggle.json to your Downloads folder
4. Place it at:   C:/Users/<YourName>/.kaggle/kaggle.json
   (the script will tell you the exact path if it can't find it)
5. Run:  pip install kaggle
6. Run:  python scripts/download_kaggle_data.py

Usage
-----
    python scripts/download_kaggle_data.py                # download all
    python scripts/download_kaggle_data.py --only resumes # resumes only
    python scripts/download_kaggle_data.py --only jobs    # jobs only
    python scripts/download_kaggle_data.py --list         # show what will be downloaded
"""

import argparse
import json
import logging
import os
import shutil
import sys
import zipfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "kaggle"

RESUME_DATASETS = [
    {
        "id": "snehaanbhawal/resume-dataset",
        "description": "Updated resume dataset (~962 resumes with categories)",
        "dest": DATA_DIR / "resumes",
        "expected_file": "UpdatedResumeDataSet.csv",
        "loader_format": "a",
    },
]

JOB_DATASETS = [
    {
        "id": "PromptCloudHQ/us-jobs-on-monstercom",
        "description": "22,000+ US job postings from Monster.com",
        "dest": DATA_DIR / "jobs",
        "expected_file": "monster_com-job_sample.csv",
        "loader_format": "a",
    },
    {
        "id": "andrewmvd/data-scientist-jobs",
        "description": "Data scientist job postings",
        "dest": DATA_DIR / "jobs",
        "expected_file": "DataScientist.csv",
        "loader_format": "b",
    },
]

ALL_DATASETS = {
    "resumes": RESUME_DATASETS,
    "jobs": JOB_DATASETS,
}


def check_kaggle_credentials() -> bool:
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        logger.info("Kaggle credentials found at: %s", kaggle_json)
        return True

    # Also check env vars (used in CI/Docker)
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        logger.info("Kaggle credentials found in environment variables.")
        return True

    logger.error(
        "\n"
        "Kaggle credentials not found.\n"
        "\n"
        "To fix this:\n"
        "  1. Go to https://www.kaggle.com/settings\n"
        "  2. Scroll to 'API' section\n"
        "  3. Click 'Create New Token'\n"
        "  4. This downloads kaggle.json to your Downloads folder\n"
        "  5. Move it to:  %s\n"
        "  6. Run this script again\n",
        Path.home() / ".kaggle" / "kaggle.json",
    )
    return False


def download_dataset(dataset: dict) -> bool:
    """Download and extract a single Kaggle dataset."""
    try:
        import kaggle
    except ImportError:
        logger.error("kaggle package not installed. Run:  pip install kaggle")
        return False

    dest: Path = dataset["dest"]
    dest.mkdir(parents=True, exist_ok=True)

    expected_file = dest / dataset["expected_file"]
    if expected_file.exists():
        logger.info("Already exists, skipping: %s", expected_file)
        return True

    dataset_id: str = dataset["id"]
    logger.info("Downloading: %s", dataset_id)

    try:
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(dataset_id, path=str(dest), unzip=True, quiet=False)
        logger.info("Downloaded to: %s", dest)
        return True
    except Exception as exc:
        logger.error("Failed to download %s: %s", dataset_id, exc)
        return False


def print_load_commands(datasets: list[dict], kind: str) -> None:
    """Print the exact commands to load each downloaded dataset."""
    script = "load_kaggle_resumes.py" if kind == "resumes" else "load_kaggle_jobs.py"
    logger.info("\n=== Commands to load %s ===", kind)
    for ds in datasets:
        file_path = ds["dest"] / ds["expected_file"]
        if file_path.exists():
            logger.info(
                "python scripts/%s --file %s --format %s --dry-run",
                script, file_path, ds["loader_format"],
            )
            logger.info(
                "python scripts/%s --file %s --format %s",
                script, file_path, ds["loader_format"],
            )


def list_datasets() -> None:
    logger.info("\n=== Resume Datasets ===")
    for ds in RESUME_DATASETS:
        status = "DOWNLOADED" if (ds["dest"] / ds["expected_file"]).exists() else "not downloaded"
        logger.info("  [%s] %s", status, ds["id"])
        logger.info("         %s", ds["description"])

    logger.info("\n=== Job Datasets ===")
    for ds in JOB_DATASETS:
        status = "DOWNLOADED" if (ds["dest"] / ds["expected_file"]).exists() else "not downloaded"
        logger.info("  [%s] %s", status, ds["id"])
        logger.info("         %s", ds["description"])


def main():
    parser = argparse.ArgumentParser(description="Download Kaggle datasets for HiringAI")
    parser.add_argument(
        "--only",
        choices=["resumes", "jobs"],
        help="Download only one category (default: both)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List datasets and their download status, then exit",
    )
    args = parser.parse_args()

    if args.list:
        list_datasets()
        return

    if not check_kaggle_credentials():
        sys.exit(1)

    targets = []
    if args.only == "resumes":
        targets = [("resumes", RESUME_DATASETS)]
    elif args.only == "jobs":
        targets = [("jobs", JOB_DATASETS)]
    else:
        targets = [("resumes", RESUME_DATASETS), ("jobs", JOB_DATASETS)]

    success = failed = skipped = 0
    for kind, datasets in targets:
        logger.info("\n--- Downloading %s datasets ---", kind)
        for ds in datasets:
            result = download_dataset(ds)
            if result:
                expected = ds["dest"] / ds["expected_file"]
                if expected.exists():
                    success += 1
                else:
                    skipped += 1
            else:
                failed += 1

    logger.info("\n=== Download summary: %d success | %d failed | %d skipped ===", success, failed, skipped)

    # Print load commands for everything that exists
    for kind, datasets in targets:
        print_load_commands(datasets, kind)


if __name__ == "__main__":
    main()
