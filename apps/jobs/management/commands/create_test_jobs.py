"""
Creates 3 synthetic test job postings for demo/testing purposes.

Usage:
    python manage.py create_test_jobs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


JOBS = [
    {
        "title": "Data Scientist – Credit Risk & AI Innovation",
        "company": "FinEdge Analytics",
        "source": "synthetic",
        "external_id": "test-job-ds-credit-risk",
        "description": (
            "We are looking for an experienced Data Scientist to join our Credit Risk & AI Innovation team. "
            "You will build explainable predictive models for credit scoring, affordability assessment, and "
            "fraud detection. You will work closely with product, engineering, and compliance teams to deliver "
            "FCA-compliant AI solutions at scale."
        ),
        "requirements": (
            "5+ years of experience in data science or machine learning.\n"
            "Strong Python skills (Pandas, NumPy, Scikit-Learn, XGBoost).\n"
            "Experience with explainability frameworks (SHAP, LIME).\n"
            "Solid understanding of credit risk modelling (PD, LGD, EAD).\n"
            "NLP and entity resolution experience.\n"
            "Familiarity with AWS and MLOps practices.\n"
            "Experience deploying models in regulated environments."
        ),
        "responsibilities": (
            "Build and maintain credit scoring and affordability models.\n"
            "Implement SHAP-based model explainability for regulatory compliance.\n"
            "Design and manage data pipelines using SQL, Spark, and Python.\n"
            "Collaborate with engineering to deploy models to AWS production.\n"
            "Conduct bias audits and fairness assessments on models.\n"
            "Mentor junior data scientists."
        ),
        "country": "United Kingdom",
        "city": "London",
        "work_model": "hybrid",
        "industry": "Financial Services",
        "job_function": "Data Science",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary_min": 70000,
        "salary_max": 95000,
        "salary_currency": "GBP",
        "skill_requirements": [
            "Python", "XGBoost", "SHAP", "LIME", "Scikit-Learn",
            "SQL", "AWS", "NLP", "entity resolution", "credit risk",
            "Pandas", "NumPy", "Docker", "MLOps",
        ],
    },
    {
        "title": "Machine Learning Engineer",
        "company": "TechNova Ltd",
        "source": "synthetic",
        "external_id": "test-job-ml-engineer",
        "description": (
            "TechNova is hiring a Machine Learning Engineer to build and deploy ML models that power "
            "our recommendation and personalisation products. You will work on the full ML lifecycle "
            "from experimentation to production deployment."
        ),
        "requirements": (
            "3+ years experience in machine learning engineering.\n"
            "Proficiency in Python, PyTorch or TensorFlow.\n"
            "Experience with model deployment (Docker, Kubernetes, CI/CD).\n"
            "Strong understanding of deep learning architectures.\n"
            "Experience with cloud platforms (AWS or GCP)."
        ),
        "responsibilities": (
            "Design, train, and deploy deep learning models.\n"
            "Build robust ML pipelines and feature stores.\n"
            "Optimise model performance and inference latency.\n"
            "Collaborate with product teams to integrate ML features."
        ),
        "country": "United Kingdom",
        "city": "Manchester",
        "work_model": "remote",
        "industry": "Technology",
        "job_function": "Machine Learning Engineering",
        "employment_type": "full_time",
        "experience_level": "mid",
        "salary_min": 60000,
        "salary_max": 80000,
        "salary_currency": "GBP",
        "skill_requirements": [
            "Python", "PyTorch", "TensorFlow", "Docker", "Kubernetes",
            "AWS", "CI/CD", "deep learning", "Pandas", "NumPy",
        ],
    },
    {
        "title": "Junior Data Analyst",
        "company": "Retail Insights Co.",
        "source": "synthetic",
        "external_id": "test-job-junior-analyst",
        "description": (
            "We are looking for a Junior Data Analyst to join our analytics team. "
            "You will analyse sales and customer data to generate actionable insights "
            "for the business. Great opportunity for someone early in their data career."
        ),
        "requirements": (
            "0–2 years experience in data analysis.\n"
            "Proficiency in SQL and Excel.\n"
            "Basic Python or R skills.\n"
            "Strong communication and presentation skills."
        ),
        "responsibilities": (
            "Produce weekly and monthly reporting dashboards.\n"
            "Conduct ad-hoc data analysis for business stakeholders.\n"
            "Maintain and improve data quality in our data warehouse.\n"
            "Assist in building customer segmentation models."
        ),
        "country": "United Kingdom",
        "city": "Bristol",
        "work_model": "onsite",
        "industry": "Retail",
        "job_function": "Data Analysis",
        "employment_type": "full_time",
        "experience_level": "entry",
        "salary_min": 28000,
        "salary_max": 38000,
        "salary_currency": "GBP",
        "skill_requirements": [
            "SQL", "Excel", "Python", "data analysis", "reporting",
        ],
    },
]


class Command(BaseCommand):
    help = "Create 3 synthetic test job postings"

    def handle(self, *args, **options):
        from apps.jobs.models import JobPost, JobSkillRequirement

        created_ids = []

        for raw in JOBS:
            skills = raw.get("skill_requirements", [])
            title = raw["title"]
            company = raw["company"]

            try:
                existing = JobPost.objects.filter(title=title, company=company).first()
                if existing:
                    self.stdout.write(f"  Already exists: {title} at {company} (id={existing.id})")
                    created_ids.append(existing.id)
                    continue

                job = JobPost.objects.create(
                    title=title,
                    company=company,
                    description=raw["description"],
                    requirements=raw.get("requirements", ""),
                    responsibilities=raw.get("responsibilities", ""),
                    country=raw.get("country", ""),
                    city=raw.get("city", ""),
                    work_model=raw.get("work_model", "onsite"),
                    industry=raw.get("industry", ""),
                    job_function=raw.get("job_function", ""),
                    employment_type=raw.get("employment_type", "full_time"),
                    experience_level=raw.get("experience_level", "mid"),
                    salary_min=raw.get("salary_min"),
                    salary_max=raw.get("salary_max"),
                    salary_currency=raw.get("salary_currency", "USD"),
                    source=raw.get("source", "synthetic"),
                    external_id=raw.get("external_id", ""),
                    is_synthetic=True,
                    status="active",
                    posted_at=timezone.now(),
                )

                for skill_name in skills:
                    JobSkillRequirement.objects.get_or_create(
                        job=job,
                        skill_name=skill_name,
                        defaults={"is_required": True},
                    )

                self.stdout.write(self.style.SUCCESS(
                    f"  Created: {job.title} at {job.company} (id={job.id}) — {len(skills)} skills"
                ))
                created_ids.append(job.id)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  FAILED [{title}]: {type(e).__name__}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_ids)} test jobs ready. IDs: {created_ids}"
        ))
