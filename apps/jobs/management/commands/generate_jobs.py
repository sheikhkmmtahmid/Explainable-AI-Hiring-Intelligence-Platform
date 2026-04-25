"""
Generates N synthetic job postings using Faker.

Usage:
    python manage.py generate_jobs           # creates 5000
    python manage.py generate_jobs --count 200
"""
import random
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

fake = Faker("en_GB")

TITLES = [
    "Data Scientist", "Senior Data Scientist", "Lead Data Scientist",
    "Machine Learning Engineer", "Senior ML Engineer", "Staff ML Engineer",
    "Data Engineer", "Senior Data Engineer", "Lead Data Engineer",
    "Data Analyst", "Senior Data Analyst", "Junior Data Analyst",
    "AI Engineer", "NLP Engineer", "Computer Vision Engineer",
    "MLOps Engineer", "Platform Engineer (ML)", "Research Scientist",
    "Quantitative Analyst", "Business Intelligence Engineer",
    "Analytics Engineer", "Applied Scientist", "Research Engineer",
    "Python Developer", "Backend Engineer (Python)", "Full Stack Engineer",
    "Software Engineer (Data)", "DevOps Engineer", "Cloud Engineer",
    "Product Analyst", "Growth Analyst", "Risk Analyst",
    "Credit Risk Data Scientist", "Fraud Data Scientist",
    "Recommendation Systems Engineer", "Search Engineer",
]

COMPANIES = [
    "FinEdge Analytics", "TechNova Ltd", "DataBridge Corp", "Insight Systems",
    "Quantum Analytics", "NexGen AI", "BlueSky Data", "CoreML Technologies",
    "DataVault Inc", "Streamline AI", "Apex Analytics", "ClearMetrics",
    "Luminary Data", "Horizon Tech", "Catalyst AI", "Meridian Systems",
    "Vertex Analytics", "Pinnacle Data", "Synapse AI", "Orbital Technologies",
    "Barclays", "HSBC", "Lloyds Bank", "NatWest", "Revolut", "Monzo",
    "Starling Bank", "ClearScore", "Experian", "Equifax",
    "Amazon", "Google", "Microsoft", "Meta", "Apple", "Deliveroo",
    "Ocado", "Babylon Health", "Checkout.com", "Wise",
    "Rolls-Royce", "BAE Systems", "AstraZeneca", "GSK", "Unilever",
    "BP", "Shell", "BT Group", "Sky", "ITV",
]

INDUSTRIES = [
    "Financial Services", "Technology", "Healthcare", "Retail",
    "Energy", "Telecommunications", "Media", "Consulting",
    "Insurance", "E-Commerce", "Logistics", "Manufacturing",
]

JOB_FUNCTIONS = [
    "Data Science", "Machine Learning Engineering", "Data Engineering",
    "Data Analysis", "Software Engineering", "AI Research",
    "Business Intelligence", "Analytics", "Platform Engineering",
]

WORK_MODELS = ["onsite", "remote", "hybrid"]
EMPLOYMENT_TYPES = ["full_time", "part_time", "contract"]
EXPERIENCE_LEVELS = ["entry", "mid", "senior", "lead"]
CURRENCIES = ["GBP", "EUR", "USD"]

SKILL_POOL = [
    "Python", "SQL", "R", "Scala", "Java", "Spark", "Kafka",
    "TensorFlow", "PyTorch", "Scikit-Learn", "XGBoost", "LightGBM",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "SHAP", "LIME", "MLflow", "Airflow", "dbt", "Looker",
    "NLP", "BERT", "GPT", "LLMs", "RAG", "transformers",
    "deep learning", "computer vision", "reinforcement learning",
    "A/B testing", "statistics", "Bayesian inference",
    "credit risk", "fraud detection", "recommendation systems",
    "CI/CD", "Git", "Agile", "MLOps", "feature engineering",
    "entity resolution", "data pipelines", "ELT/ETL", "Tableau",
]

SALARY_RANGES = {
    "entry": (25000, 45000),
    "mid":   (45000, 75000),
    "senior": (70000, 110000),
    "lead":  (90000, 150000),
}


def random_skills(n=None):
    n = n or random.randint(4, 12)
    return random.sample(SKILL_POOL, min(n, len(SKILL_POOL)))


def make_description(title, company, industry):
    return (
        f"{company} is looking for a talented {title} to join our {industry} team. "
        f"You will work on challenging problems involving large-scale data, building and deploying "
        f"machine learning models, and collaborating with cross-functional teams. "
        f"{fake.paragraph(nb_sentences=3)}"
    )


def make_requirements(skills):
    lines = [
        f"Experience with {s}." for s in random.sample(skills, min(len(skills), 5))
    ]
    lines += [
        fake.sentence(),
        fake.sentence(),
    ]
    return "\n".join(lines)


def make_responsibilities():
    return "\n".join(fake.sentence() for _ in range(random.randint(4, 7)))


class Command(BaseCommand):
    help = "Generate N synthetic job postings"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=5000)
        parser.add_argument("--batch", type=int, default=500)

    def handle(self, *args, **options):
        from apps.jobs.models import JobPost, JobSkillRequirement

        total = options["count"]
        batch_size = options["batch"]

        self.stdout.write(f"Generating {total} synthetic jobs...")

        jobs_to_create = []
        for i in range(total):
            exp = random.choice(EXPERIENCE_LEVELS)
            sal_min, sal_max = SALARY_RANGES[exp]
            currency = random.choice(CURRENCIES)
            title = random.choice(TITLES)
            company = random.choice(COMPANIES)
            industry = random.choice(INDUSTRIES)

            jobs_to_create.append(JobPost(
                title=title,
                company=company,
                description=make_description(title, company, industry),
                requirements=make_requirements(random_skills()),
                responsibilities=make_responsibilities(),
                country=fake.country(),
                city=fake.city(),
                work_model=random.choice(WORK_MODELS),
                industry=industry,
                job_function=random.choice(JOB_FUNCTIONS),
                employment_type=random.choice(EMPLOYMENT_TYPES),
                experience_level=exp,
                salary_min=random.randint(sal_min, sal_max),
                salary_max=random.randint(sal_min, sal_max) + random.randint(5000, 20000),
                salary_currency=currency,
                source="synthetic",
                external_id=str(uuid.uuid4()),
                is_synthetic=True,
                status="active",
                posted_at=fake.date_time_between(start_date="-1y", end_date="now", tzinfo=timezone.utc),
            ))

        # Bulk create in batches
        created_count = 0
        for start in range(0, len(jobs_to_create), batch_size):
            batch = jobs_to_create[start:start + batch_size]
            created = JobPost.objects.bulk_create(batch, ignore_conflicts=True)
            created_count += len(created)
            self.stdout.write(f"  Inserted batch {start // batch_size + 1}: {created_count}/{total}")

        # Add skills to created jobs (fetch IDs of synthetic jobs without skills)
        self.stdout.write("Adding skill requirements...")
        jobs_without_skills = JobPost.objects.filter(
            source="synthetic", is_synthetic=True, skill_requirements__isnull=True
        ).distinct()

        skill_objs = []
        for job in jobs_without_skills.iterator(chunk_size=500):
            for skill_name in random_skills():
                skill_objs.append(JobSkillRequirement(
                    job=job, skill_name=skill_name, is_required=random.choice([True, False])
                ))
            if len(skill_objs) >= 2000:
                JobSkillRequirement.objects.bulk_create(skill_objs, ignore_conflicts=True)
                skill_objs = []

        if skill_objs:
            JobSkillRequirement.objects.bulk_create(skill_objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_count} jobs created."))
