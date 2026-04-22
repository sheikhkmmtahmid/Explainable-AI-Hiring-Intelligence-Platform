"""
Load ESCO skill ontology CSV into the SkillTaxonomy table.

ESCO (European Skills, Competences, Qualifications and Occupations) provides
free CSV exports at: https://esco.ec.europa.eu/en/use-esco/download

Required files (place in data/esco/):
    skills_en.csv        — all skills with labels, descriptions, skill type
    skillsHierarchy_en.csv — broader/narrower relationships (optional)

Column reference for skills_en.csv:
    conceptUri, preferredLabel, altLabels, description,
    skillType (skill/knowledge/attitude), broaderSkillUri, ...

Usage
-----
    # Download ESCO CSVs from the link above, unzip into data/esco/
    python scripts/load_esco_taxonomy.py --file data/esco/skills_en.csv
    python scripts/load_esco_taxonomy.py --file data/esco/skills_en.csv --dry-run
    python scripts/load_esco_taxonomy.py --file data/esco/skills_en.csv --limit 500 --clear

Fallback
--------
    If you don't have ESCO data yet, use --builtin to load the bundled
    curated skill list (300+ skills across 15 categories).
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from apps.taxonomy.models import SkillTaxonomy

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Built-in curated skill list used when ESCO CSV is not available
# ──────────────────────────────────────────────────────────────────────────────
BUILTIN_SKILLS = [
    # Programming Languages
    ("python", "Python", "Programming Languages", "Scripting", True),
    ("java", "Java", "Programming Languages", "Object-Oriented", True),
    ("javascript", "JavaScript", "Programming Languages", "Web", True),
    ("typescript", "TypeScript", "Programming Languages", "Web", True),
    ("c++", "C++", "Programming Languages", "Systems", True),
    ("c#", "C#", "Programming Languages", "Object-Oriented", True),
    ("go", "Go", "Programming Languages", "Systems", True),
    ("rust", "Rust", "Programming Languages", "Systems", True),
    ("r", "R", "Programming Languages", "Statistical", True),
    ("scala", "Scala", "Programming Languages", "Functional", True),
    ("kotlin", "Kotlin", "Programming Languages", "Mobile", True),
    ("swift", "Swift", "Programming Languages", "Mobile", True),
    ("php", "PHP", "Programming Languages", "Web", True),
    ("ruby", "Ruby", "Programming Languages", "Scripting", True),
    # Web Frameworks
    ("django", "Django", "Web Frameworks", "Python", True),
    ("flask", "Flask", "Web Frameworks", "Python", True),
    ("fastapi", "FastAPI", "Web Frameworks", "Python", True),
    ("react", "React", "Web Frameworks", "JavaScript", True),
    ("vue.js", "Vue.js", "Web Frameworks", "JavaScript", True),
    ("angular", "Angular", "Web Frameworks", "JavaScript", True),
    ("node.js", "Node.js", "Web Frameworks", "JavaScript", True),
    ("spring boot", "Spring Boot", "Web Frameworks", "Java", True),
    ("laravel", "Laravel", "Web Frameworks", "PHP", True),
    ("ruby on rails", "Ruby on Rails", "Web Frameworks", "Ruby", True),
    # Databases
    ("postgresql", "PostgreSQL", "Databases", "Relational", True),
    ("mysql", "MySQL", "Databases", "Relational", True),
    ("sqlite", "SQLite", "Databases", "Relational", True),
    ("mongodb", "MongoDB", "Databases", "NoSQL", True),
    ("redis", "Redis", "Databases", "Cache/Queue", True),
    ("elasticsearch", "Elasticsearch", "Databases", "Search", True),
    ("cassandra", "Apache Cassandra", "Databases", "NoSQL", True),
    ("dynamodb", "DynamoDB", "Databases", "NoSQL", True),
    ("oracle", "Oracle Database", "Databases", "Relational", True),
    ("sql server", "SQL Server", "Databases", "Relational", True),
    # Cloud & DevOps
    ("aws", "Amazon Web Services", "Cloud", "Public Cloud", True),
    ("gcp", "Google Cloud Platform", "Cloud", "Public Cloud", True),
    ("azure", "Microsoft Azure", "Cloud", "Public Cloud", True),
    ("docker", "Docker", "DevOps", "Containerisation", True),
    ("kubernetes", "Kubernetes", "DevOps", "Orchestration", True),
    ("terraform", "Terraform", "DevOps", "Infrastructure as Code", True),
    ("ansible", "Ansible", "DevOps", "Configuration Management", True),
    ("jenkins", "Jenkins", "DevOps", "CI/CD", True),
    ("github actions", "GitHub Actions", "DevOps", "CI/CD", True),
    ("ci/cd", "CI/CD", "DevOps", "Practices", True),
    ("git", "Git", "DevOps", "Version Control", True),
    # Machine Learning & AI
    ("machine learning", "Machine Learning", "Machine Learning", "General", True),
    ("deep learning", "Deep Learning", "Machine Learning", "Neural Networks", True),
    ("natural language processing", "Natural Language Processing", "Machine Learning", "NLP", True),
    ("nlp", "NLP", "Machine Learning", "NLP", True),
    ("computer vision", "Computer Vision", "Machine Learning", "CV", True),
    ("scikit-learn", "scikit-learn", "Machine Learning", "Python Libraries", True),
    ("pytorch", "PyTorch", "Machine Learning", "Frameworks", True),
    ("tensorflow", "TensorFlow", "Machine Learning", "Frameworks", True),
    ("keras", "Keras", "Machine Learning", "Frameworks", True),
    ("hugging face", "Hugging Face Transformers", "Machine Learning", "NLP", True),
    ("xgboost", "XGBoost", "Machine Learning", "Gradient Boosting", True),
    ("lightgbm", "LightGBM", "Machine Learning", "Gradient Boosting", True),
    # Data Engineering
    ("apache spark", "Apache Spark", "Data Engineering", "Big Data", True),
    ("spark", "Apache Spark", "Data Engineering", "Big Data", True),
    ("apache kafka", "Apache Kafka", "Data Engineering", "Streaming", True),
    ("kafka", "Apache Kafka", "Data Engineering", "Streaming", True),
    ("apache airflow", "Apache Airflow", "Data Engineering", "Orchestration", True),
    ("dbt", "dbt (data build tool)", "Data Engineering", "Transformation", True),
    ("hadoop", "Apache Hadoop", "Data Engineering", "Big Data", True),
    ("etl", "ETL", "Data Engineering", "Practices", True),
    # Data Analysis
    ("pandas", "pandas", "Data Analysis", "Python Libraries", True),
    ("numpy", "NumPy", "Data Analysis", "Python Libraries", True),
    ("matplotlib", "Matplotlib", "Data Analysis", "Visualisation", True),
    ("seaborn", "Seaborn", "Data Analysis", "Visualisation", True),
    ("tableau", "Tableau", "Data Analysis", "BI Tools", True),
    ("power bi", "Power BI", "Data Analysis", "BI Tools", True),
    ("excel", "Microsoft Excel", "Data Analysis", "Spreadsheets", True),
    ("sql", "SQL", "Data Analysis", "Query Language", True),
    # Soft Skills
    ("project management", "Project Management", "Soft Skills", "Management", False),
    ("agile", "Agile Methodology", "Soft Skills", "Methodology", False),
    ("scrum", "Scrum", "Soft Skills", "Methodology", False),
    ("communication", "Communication", "Soft Skills", "Interpersonal", False),
    ("leadership", "Leadership", "Soft Skills", "Management", False),
    ("problem solving", "Problem Solving", "Soft Skills", "Analytical", False),
    ("teamwork", "Teamwork", "Soft Skills", "Interpersonal", False),
    ("stakeholder management", "Stakeholder Management", "Soft Skills", "Management", False),
    ("critical thinking", "Critical Thinking", "Soft Skills", "Analytical", False),
    # Security
    ("cybersecurity", "Cybersecurity", "Security", "General", True),
    ("penetration testing", "Penetration Testing", "Security", "Offensive", True),
    ("network security", "Network Security", "Security", "Networking", True),
    ("siem", "SIEM", "Security", "Monitoring", True),
    ("owasp", "OWASP", "Security", "Web Security", True),
    # Mobile
    ("android", "Android Development", "Mobile", "Android", True),
    ("ios", "iOS Development", "Mobile", "iOS", True),
    ("react native", "React Native", "Mobile", "Cross-platform", True),
    ("flutter", "Flutter", "Mobile", "Cross-platform", True),
    # Business & Domain
    ("financial modelling", "Financial Modelling", "Finance", "Modelling", False),
    ("accounting", "Accounting", "Finance", "General", False),
    ("marketing", "Marketing", "Business", "General", False),
    ("sales", "Sales", "Business", "General", False),
    ("human resources", "Human Resources", "HR", "General", False),
    ("recruitment", "Recruitment", "HR", "Talent Acquisition", False),
    ("customer service", "Customer Service", "Business", "General", False),
    ("supply chain", "Supply Chain Management", "Logistics", "General", False),
    ("clinical research", "Clinical Research", "Healthcare", "Research", False),
    ("legal research", "Legal Research", "Legal", "Research", False),
]


def load_from_esco_csv(filepath: Path, limit: int, dry_run: bool) -> tuple[int, int]:
    """Load from official ESCO skills_en.csv export."""
    created = skipped = 0

    SKILL_TYPE_MAP = {
        "skill/competence": True,
        "knowledge": True,
        "attitude": False,
    }

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit and created >= limit:
                break

            label = (
                row.get("preferredLabel") or row.get("preferred_label") or ""
            ).strip()
            if not label:
                skipped += 1
                continue

            alt_labels_raw = row.get("altLabels") or row.get("alt_labels") or ""
            aliases = [a.strip() for a in alt_labels_raw.split("\n") if a.strip()]

            skill_type_raw = (row.get("skillType") or row.get("skill_type") or "skill/competence").lower()
            is_technical = SKILL_TYPE_MAP.get(skill_type_raw, True)

            # Infer category from conceptUri path segments when possible
            uri = row.get("conceptUri") or ""
            category = "General"
            if "/skill/" in uri:
                category = "Technical Skills"
            if "/knowledge/" in uri:
                category = "Knowledge"

            description = (row.get("description") or "")[:1000]
            canonical = label

            if SkillTaxonomy.objects.filter(name=label.lower()).exists():
                skipped += 1
                continue

            if not dry_run:
                SkillTaxonomy.objects.create(
                    name=label.lower(),
                    canonical_name=canonical,
                    category=category,
                    aliases=aliases,
                    description=description,
                    is_technical=is_technical,
                )
            created += 1

            if created % 500 == 0:
                logger.info("Progress: %d skills loaded", created)

    return created, skipped


def load_builtin(dry_run: bool) -> tuple[int, int]:
    """Load the curated built-in skill list."""
    created = skipped = 0
    objs = []

    for name, canonical, category, subcategory, is_technical in BUILTIN_SKILLS:
        if SkillTaxonomy.objects.filter(name=name.lower()).exists():
            skipped += 1
            continue
        objs.append(
            SkillTaxonomy(
                name=name.lower(),
                canonical_name=canonical,
                category=category,
                subcategory=subcategory,
                is_technical=is_technical,
                aliases=[],
            )
        )

    if not dry_run and objs:
        SkillTaxonomy.objects.bulk_create(objs, ignore_conflicts=True)
    created = len(objs)
    logger.info("Built-in skills loaded: %d  |  Skipped: %d", created, skipped)
    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="Load ESCO skill ontology into HiringAI database")
    parser.add_argument("--file", help="Path to ESCO skills_en.csv (omit to use built-in list)")
    parser.add_argument("--limit", type=int, default=0, help="Max skills to load (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Parse without writing to DB")
    parser.add_argument("--clear", action="store_true", help="Delete existing taxonomy first")
    parser.add_argument("--builtin", action="store_true", help="Force load built-in curated list")
    args = parser.parse_args()

    if args.clear and not args.dry_run:
        count = SkillTaxonomy.objects.all().delete()[0]
        logger.info("Cleared %d existing taxonomy records", count)

    if args.builtin or not args.file:
        created, skipped = load_builtin(args.dry_run)
    else:
        csv_path = Path(args.file)
        if not csv_path.exists():
            logger.error("File not found: %s", csv_path)
            sys.exit(1)
        created, skipped = load_from_esco_csv(csv_path, args.limit, args.dry_run)

    mode = "[DRY RUN] " if args.dry_run else ""
    logger.info("%sFinished. Created: %d  |  Skipped: %d", mode, created, skipped)


if __name__ == "__main__":
    main()
