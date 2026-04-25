"""
Generates N diverse synthetic candidates with skills and SBERT embeddings.

Usage:
    python manage.py generate_candidates           # creates 26
    python manage.py generate_candidates --count 50
    python manage.py generate_candidates --count 26 --no-embeddings
"""
import random
from django.core.management.base import BaseCommand
from faker import Faker

fake = Faker("en_GB")

TITLES = [
    "Data Scientist", "Senior Data Scientist", "Machine Learning Engineer",
    "Data Analyst", "Senior Data Analyst", "Data Engineer", "Senior Data Engineer",
    "AI Engineer", "NLP Engineer", "ML Researcher", "Business Intelligence Analyst",
    "Analytics Engineer", "Applied Scientist", "Quantitative Analyst",
    "Junior Data Scientist", "Python Developer", "Software Engineer",
    "Credit Risk Analyst", "Fraud Analyst", "Research Scientist",
]

EDUCATION_FIELDS = [
    "Computer Science", "Data Science", "Mathematics", "Statistics",
    "Artificial Intelligence", "Machine Learning", "Physics",
    "Information Systems", "Software Engineering", "Economics",
    "Electrical Engineering", "Cognitive Science",
]

EDUCATION_LEVELS = ["bachelor", "master", "phd", "bachelor", "master"]

SENIORITY_MAP = {
    (0, 1.5): ("junior", "entry"),
    (1.5, 4): ("mid", "mid"),
    (4, 7): ("senior", "senior"),
    (7, 15): ("lead", "lead"),
}

GENDERS = ["male", "female", "female", "male", "non_binary"]
AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"]
ETHNICITIES = [
    "White", "Asian", "Black", "Hispanic", "Mixed",
    "South Asian", "East Asian", "Middle Eastern", "Other",
]

SKILL_POOL = [
    "Python", "SQL", "R", "Scala", "Java", "Spark", "Kafka",
    "TensorFlow", "PyTorch", "Scikit-Learn", "XGBoost", "LightGBM",
    "Pandas", "NumPy", "Matplotlib", "Seaborn",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes",
    "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "SHAP", "LIME", "MLflow", "Airflow", "dbt",
    "NLP", "BERT", "transformers", "spaCy",
    "deep learning", "computer vision", "reinforcement learning",
    "A/B testing", "statistics", "Bayesian inference",
    "credit risk", "fraud detection", "recommendation systems",
    "CI/CD", "Git", "Agile", "MLOps", "feature engineering",
    "Tableau", "Power BI", "Looker", "Excel",
]

CURRENCIES = ["GBP", "EUR", "USD"]
REMOTE_PREFS = ["remote", "hybrid", "onsite", "flexible"]
AVAILABILITY = ["actively_looking", "open", "open", "actively_looking", "not_looking"]


def get_seniority(yoe):
    for (lo, hi), (seniority, _) in SENIORITY_MAP.items():
        if lo <= yoe < hi:
            return seniority
    return "lead"


def make_cv_text(name, title, yoe, education, education_field, skills, city, country):
    skill_str = ", ".join(skills[:10])
    return f"""{name.upper()}
{title}
{city}, {country} | {fake.email()}

PROFESSIONAL SUMMARY
{title} with {yoe:.0f} years of experience. {fake.paragraph(nb_sentences=2)}

EXPERIENCE
{title} — {fake.company()} ({fake.year()}–Present)
{fake.paragraph(nb_sentences=3)}

{fake.job()} — {fake.company()} ({int(fake.year()) - 3}–{int(fake.year()) - 1})
{fake.paragraph(nb_sentences=2)}

EDUCATION
{education.replace('_', "'s'").title()} {education_field} — {fake.company() + " University"}, {fake.year()}

SKILLS
{skill_str}
"""


class Command(BaseCommand):
    help = "Generate N diverse synthetic candidates"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=26)
        parser.add_argument("--no-embeddings", action="store_true")

    def handle(self, *args, **options):
        from apps.candidates.models import Candidate, CandidateSkill
        from apps.parsing.services import parse_cv_text

        count = options["count"]
        skip_embeddings = options["no_embeddings"]

        self.stdout.write(f"Generating {count} synthetic candidates...")

        created_ids = []

        for i in range(count):
            yoe = round(random.uniform(0.5, 14), 1)
            seniority = get_seniority(yoe)
            title = random.choice(TITLES)
            education = random.choice(EDUCATION_LEVELS)
            education_field = random.choice(EDUCATION_FIELDS)
            country = fake.country()
            city = fake.city()
            skills = random.sample(SKILL_POOL, random.randint(5, 14))
            sal_base = int(25000 + yoe * 5000)
            currency = random.choice(CURRENCIES)

            name = fake.name()
            email = f"synthetic.{fake.uuid4()[:8]}@candidate.dev"

            cv_text = make_cv_text(name, title, yoe, education, education_field, skills, city, country)

            try:
                candidate = Candidate.objects.create(
                    full_name=name,
                    email=email,
                    phone=fake.phone_number()[:30],
                    current_title=title,
                    years_of_experience=yoe,
                    seniority_level=seniority,
                    highest_education=education,
                    education_field=education_field,
                    country=country,
                    city=city,
                    remote_preference=random.choice(REMOTE_PREFS),
                    availability_status=random.choice(AVAILABILITY),
                    expected_salary_min=sal_base,
                    expected_salary_max=sal_base + random.randint(5000, 20000),
                    salary_currency=currency,
                    gender=random.choice(GENDERS),
                    age_range=random.choice(AGE_RANGES),
                    ethnicity=random.choice(ETHNICITIES),
                    disability_status=random.choice([True, False, None]),
                    summary=fake.paragraph(nb_sentences=3),
                    raw_cv_text=cv_text,
                    is_synthetic=True,
                )

                # Add skills
                for skill_name in skills:
                    CandidateSkill.objects.get_or_create(
                        candidate=candidate,
                        skill_name=skill_name,
                        defaults={"source": "manual", "proficiency": random.choice(["beginner", "intermediate", "advanced"])},
                    )

                created_ids.append(candidate.id)

                if (i + 1) % 5 == 0:
                    self.stdout.write(f"  Created {i + 1}/{count}...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed [{name}]: {e}"))

        # Generate SBERT embeddings
        if not skip_embeddings and created_ids:
            self.stdout.write(f"\nGenerating SBERT embeddings for {len(created_ids)} candidates...")
            from apps.candidates.models import CandidateEmbedding
            from ml.embeddings.encoder import encode_text, get_model_name
            from apps.matching.tasks import _build_candidate_text

            for idx, cid in enumerate(created_ids):
                try:
                    from apps.candidates.models import Candidate
                    c = Candidate.objects.prefetch_related("skills").get(id=cid)
                    vector = encode_text(_build_candidate_text(c))
                    CandidateEmbedding.objects.update_or_create(
                        candidate=c,
                        defaults={"vector": vector.tolist(), "model_name": get_model_name()},
                    )
                    if (idx + 1) % 5 == 0:
                        self.stdout.write(f"  Embeddings: {idx + 1}/{len(created_ids)}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Embedding failed for {cid}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_ids)} candidates created in TiDB Cloud."
        ))
