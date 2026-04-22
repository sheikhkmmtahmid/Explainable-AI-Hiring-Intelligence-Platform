"""
Creates 4 synthetic test candidates at varying match levels for the
"Data Scientist – Credit Risk & AI Innovation" job description.

Usage:
    python manage.py create_test_candidates
    python manage.py create_test_candidates --job-id 123   # attach to specific job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


CVS = {
    "aisha_okonkwo": {
        "full_name": "Aisha Okonkwo",
        "email": "aisha.okonkwo@testcandidate.dev",
        "phone": "+44 7700 100001",
        "current_title": "Senior Data Scientist",
        "years_of_experience": 6.0,
        "highest_education": "master",
        "education_field": "Data Science",
        "city": "London",
        "country": "United Kingdom",
        "availability_status": "actively_looking",
        "expected_salary_min": 65000,
        "expected_salary_max": 80000,
        "salary_currency": "GBP",
        "summary": (
            "Senior Data Scientist with 6 years of experience in fintech and credit risk. "
            "Expert in building explainable predictive models using SHAP and LIME. "
            "Deep expertise in Python, scikit-learn, XGBoost, and NLP-based entity resolution. "
            "Led affordability and fraud detection models at Experian and ClearScore."
        ),
        "cv_text": """\
AISHA OKONKWO
Senior Data Scientist | Credit Risk & Explainable AI
London, UK | aisha.okonkwo@testcandidate.dev | +44 7700 100001

PROFESSIONAL SUMMARY
Senior Data Scientist with 6+ years of experience in fintech and credit risk modelling.
Specialist in explainable AI using SHAP and LIME, with deep expertise in building and
deploying Linear Regression, Logistic Regression, and XGBoost models into high-scale AWS
production environments. Proven track record in NLP-based entity resolution and fraud detection.

EXPERIENCE

Senior Data Scientist — ClearScore, London (2021–Present)
- Built affordability and income estimation models using Linear Regression and XGBoost,
  reducing loan default rates by 18%.
- Developed entity resolution pipeline using fuzzy matching and named entity recognition (NER)
  to deduplicate 50M+ consumer records.
- Implemented SHAP-based model explainability framework ensuring FCA regulatory compliance.
- Deployed models to AWS using Docker and Kubernetes with CI/CD pipelines via GitHub Actions.
- Used LLM APIs (OpenAI GPT-4) for context engineering on unstructured transaction data.

Data Scientist — Experian, Nottingham (2019–2021)
- Designed credit risk scoring models combining Logistic Regression and gradient boosting (XGBoost).
- Built data pipelines using SQL, Spark, and Python (Pandas, NumPy, Scikit-Learn).
- Conducted behavioural signal analysis: spending volatility, income stability patterns.
- Applied NLP for transaction categorisation and merchant entity matching.

Junior Data Scientist — Lloyds Banking Group (2018–2019)
- Supported fraud detection model development using machine learning and data analysis.
- SQL-based feature engineering on large transactional datasets.

EDUCATION
MSc Data Science — University College London (UCL), 2018
BSc Mathematics & Statistics — University of Warwick, 2017

SKILLS
Python (expert): Pandas, NumPy, Scikit-Learn, XGBoost, LightGBM
Machine Learning: Linear Regression, Logistic Regression, Gradient Boosting, Random Forest
Explainability: SHAP, LIME
NLP: entity resolution, fuzzy matching, named entity recognition, spaCy
GenAI: LLM APIs, prompt engineering, context engineering
Cloud: AWS (SageMaker, S3, Lambda), Docker, Kubernetes
Data: SQL, PostgreSQL, Spark, Kafka
Practices: CI/CD, Agile, Git, MLOps

CERTIFICATIONS
AWS Certified Machine Learning Specialty
""",
    },

    "james_chen": {
        "full_name": "James Chen",
        "email": "james.chen@testcandidate.dev",
        "phone": "+44 7700 100002",
        "current_title": "Data Scientist",
        "years_of_experience": 4.0,
        "highest_education": "bachelor",
        "education_field": "Computer Science",
        "city": "Manchester",
        "country": "United Kingdom",
        "availability_status": "open",
        "expected_salary_min": 55000,
        "expected_salary_max": 70000,
        "salary_currency": "GBP",
        "summary": (
            "Data Scientist with 4 years of experience in e-commerce and retail analytics. "
            "Strong Python and machine learning skills. No direct credit risk or fintech experience."
        ),
        "cv_text": """\
JAMES CHEN
Data Scientist
Manchester, UK | james.chen@testcandidate.dev | +44 7700 100002

PROFESSIONAL SUMMARY
Data Scientist with 4 years of experience building recommendation systems and customer
segmentation models in e-commerce. Proficient in Python, machine learning, and data analysis.
Strong SQL and data engineering skills. No prior fintech or credit risk background but eager
to transition into financial services.

EXPERIENCE

Data Scientist — ASOS, Manchester (2021–Present)
- Built customer churn prediction models using Logistic Regression and Random Forest.
- Developed product recommendation engine using collaborative filtering and deep learning (PyTorch).
- Analysed customer spending patterns and behavioural clusters using Python, Pandas, NumPy.
- Delivered A/B test analysis and statistical significance testing using scikit-learn.

Junior Data Analyst — Booking.com (2020–2021)
- SQL-based reporting and data pipeline development using PostgreSQL and Python.
- Exploratory data analysis and visualisation for marketing campaigns.
- Machine learning models for price optimisation.

EDUCATION
BSc Computer Science — University of Manchester, 2020

SKILLS
Python: Pandas, NumPy, Scikit-Learn, PyTorch, TensorFlow
Machine Learning: Logistic Regression, Random Forest, Gradient Boosting
NLP: basic text classification, sentiment analysis
Data: SQL, PostgreSQL, MongoDB
Cloud: AWS (basic EC2, S3), Docker
Practices: Git, Agile, Scrum
No SHAP or explainability framework experience.
No entity resolution or credit risk experience.
""",
    },

    "priya_sharma": {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@testcandidate.dev",
        "phone": "+44 7700 100003",
        "current_title": "ML Engineer",
        "years_of_experience": 2.5,
        "highest_education": "master",
        "education_field": "Artificial Intelligence",
        "city": "Edinburgh",
        "country": "United Kingdom",
        "availability_status": "open",
        "expected_salary_min": 50000,
        "expected_salary_max": 65000,
        "salary_currency": "GBP",
        "summary": (
            "ML Engineer with 2.5 years specialising in deep learning and LLMs. "
            "Strong Python and GenAI skills. No credit risk, SHAP, or entity resolution experience. "
            "Primarily focused on computer vision and generative AI applications."
        ),
        "cv_text": """\
PRIYA SHARMA
ML Engineer — Deep Learning & Generative AI
Edinburgh, UK | priya.sharma@testcandidate.dev | +44 7700 100003

PROFESSIONAL SUMMARY
ML Engineer with 2.5 years of experience deploying deep learning and generative AI models.
Specialist in LLM APIs, prompt engineering, and computer vision. Strong Python engineering
skills. Background is primarily in unstructured data and neural networks rather than
classical statistics or credit risk.

EXPERIENCE

ML Engineer — Skyscanner, Edinburgh (2022–Present)
- Built and deployed computer vision models using PyTorch and TensorFlow for image recognition.
- Integrated LLM APIs (OpenAI, Anthropic) for customer-facing GenAI features.
- Prompt engineering and context engineering for retrieval-augmented generation (RAG) pipelines.
- Containerised models using Docker and deployed on AWS with CI/CD automation.

Graduate ML Engineer — FanDuel, Edinburgh (2021–2022)
- Developed recommendation models using deep learning and collaborative filtering.
- Python data pipelines with Pandas and NumPy.
- Some NLP work: text classification and sentiment analysis using transformers.

EDUCATION
MSc Artificial Intelligence — University of Edinburgh, 2021
BSc Computer Science — Heriot-Watt University, 2020

SKILLS
Python: Pandas, NumPy, PyTorch, TensorFlow, Hugging Face
Deep Learning: CNNs, Transformers, LLMs
GenAI: LLM APIs, prompt engineering, context engineering, RAG
NLP: transformers, text classification (no entity resolution or fuzzy matching)
Cloud: AWS, Docker, Kubernetes, CI/CD
Data: SQL (basic), Git, Agile
Gap: No SHAP, no XGBoost, no Logistic Regression, no credit risk, no fintech experience.
Gap: No entity resolution, no fraud detection, no affordability modelling.
""",
    },

    "tom_williams": {
        "full_name": "Tom Williams",
        "email": "tom.williams@testcandidate.dev",
        "phone": "+44 7700 100004",
        "current_title": "Junior Software Developer",
        "years_of_experience": 1.0,
        "highest_education": "bachelor",
        "education_field": "Mathematics",
        "city": "Bristol",
        "country": "United Kingdom",
        "availability_status": "actively_looking",
        "expected_salary_min": 30000,
        "expected_salary_max": 40000,
        "salary_currency": "GBP",
        "summary": (
            "Junior Software Developer with a Mathematics degree and 1 year of web development experience. "
            "No machine learning or data science experience beyond university coursework."
        ),
        "cv_text": """\
TOM WILLIAMS
Junior Software Developer
Bristol, UK | tom.williams@testcandidate.dev | +44 7700 100004

PROFESSIONAL SUMMARY
Junior Software Developer with 1 year of professional experience in web application
development. BSc Mathematics graduate with a theoretical background in statistics.
Enthusiastic about data science and keen to develop machine learning skills. Currently
completing online courses in Python and data analysis.

EXPERIENCE

Junior Software Developer — Local Web Agency, Bristol (2024–Present)
- Built web applications using JavaScript, React, and Node.js.
- Basic Python scripting for data export and automation tasks.
- SQL queries for database reporting (MySQL).
- Worked in Agile/Scrum teams with Git version control.

EDUCATION
BSc Mathematics — University of Bristol, 2023
Modules: Linear Algebra, Statistics, Probability Theory, Calculus
Final Year Project: Statistical analysis of financial time series (R)

SKILLS
Programming: Python (beginner), JavaScript, React, Node.js
Data: SQL (basic MySQL), Excel
Statistics: linear models (academic only), basic probability
Machine Learning: completed Coursera ML course (Andrew Ng) — no professional experience
Tools: Git, Docker (basic), Agile, Scrum
Gaps: No professional data science, no machine learning deployment, no fintech,
no SHAP, no XGBoost, no Pandas/NumPy at professional level, no NLP, no AWS.
""",
    },
}


class Command(BaseCommand):
    help = "Create 4 synthetic test candidates for the Credit Risk Data Scientist job"

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, default=None,
                            help="Job ID to trigger matching against after creation")

    def handle(self, *args, **options):
        from apps.candidates.models import Candidate, CandidateCV
        from apps.candidates.services import attach_cv, add_skill
        from apps.parsing.services import parse_cv_text

        created_ids = []

        for key, info in CVS.items():
            email = info["email"]

            # Skip if already exists
            if Candidate.objects.filter(email=email).exists():
                c = Candidate.objects.get(email=email)
                self.stdout.write(f"  Already exists: {info['full_name']} (id={c.id})")
                created_ids.append(c.id)
                continue

            c = Candidate.objects.create(
                full_name=info["full_name"],
                email=email,
                phone=info["phone"],
                current_title=info["current_title"],
                years_of_experience=info["years_of_experience"],
                highest_education=info["highest_education"],
                education_field=info["education_field"],
                city=info["city"],
                country=info["country"],
                availability_status=info["availability_status"],
                expected_salary_min=info["expected_salary_min"],
                expected_salary_max=info["expected_salary_max"],
                salary_currency=info["salary_currency"],
                summary=info["summary"],
                is_synthetic=True,
            )

            # Wrap CV text in a Django ContentFile so attach_cv can save it properly
            try:
                from django.core.files.base import ContentFile
                cv_file = ContentFile(info["cv_text"].encode("utf-8"), name=f"{key}_cv.txt")
                cv = attach_cv(c, cv_file, f"{key}_cv.txt")

                # Store raw text directly (skip async parsing, run inline)
                cv.raw_text = info["cv_text"]
                cv.parsed_at = timezone.now()
                cv.save(update_fields=["raw_text", "parsed_at"])

                c.raw_cv_text = info["cv_text"]
                c.save(update_fields=["raw_cv_text"])

                # Extract and save skills synchronously
                parsed = parse_cv_text(info["cv_text"])
                for skill_data in parsed.get("skills", []):
                    add_skill(c, source="cv_parsed", **skill_data)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  CV attach failed for {info['full_name']}: {e}"))

            created_ids.append(c.id)
            skill_count = c.skills.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created: {c.full_name} (id={c.id}) — {skill_count} skills extracted"
                )
            )

        # Generate embeddings for all created candidates
        self.stdout.write("\nGenerating SBERT embeddings…")
        from apps.candidates.models import Candidate, CandidateEmbedding
        from ml.embeddings.encoder import encode_text, get_model_name
        from apps.matching.tasks import _build_candidate_text
        for cid in created_ids:
            try:
                candidate = Candidate.objects.prefetch_related("skills", "experiences").get(id=cid)
                vector = encode_text(_build_candidate_text(candidate))
                CandidateEmbedding.objects.update_or_create(
                    candidate=candidate,
                    defaults={"vector": vector.tolist(), "model_name": get_model_name()},
                )
                self.stdout.write(f"  Embedding generated for candidate {cid}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Embedding failed for {cid}: {e}"))

        # Trigger matching if job-id provided
        job_id = options.get("job_id")
        if job_id:
            self.stdout.write(f"\nTriggering batch matching for job {job_id}…")
            from apps.matching.services import run_batch_matching_for_job
            try:
                count = run_batch_matching_for_job(job_id)
                self.stdout.write(self.style.SUCCESS(f"  Matching complete — {count} results."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Matching failed: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_ids)} test candidates ready."
            f"\nCandidate IDs: {created_ids}"
            + (f"\nNow open http://localhost:3000/matching/{job_id} to see results." if job_id else
               "\nRe-run with --job-id <id> to auto-trigger matching.")
        ))
