"""
Seeds SkillTaxonomy with a consolidated skill vocabulary, built from the
skill lists already used across the project's synthetic data generators
and CV parser, organised into categories with common aliases.

This taxonomy is the source of truth for the spaCy PhraseMatcher-based
skill extractor in apps.parsing.services -- adding a new skill here makes
it detectable in CVs immediately, without touching extraction code.

Usage:
    python manage.py seed_skill_taxonomy
"""
from django.core.management.base import BaseCommand

# (canonical_name, category, is_technical, aliases)
SKILLS = [
    # Programming languages
    ("Python", "Programming Languages", True, []),
    ("Java", "Programming Languages", True, []),
    ("JavaScript", "Programming Languages", True, ["JS", "ECMAScript"]),
    ("TypeScript", "Programming Languages", True, ["TS"]),
    ("SQL", "Programming Languages", True, ["Structured Query Language"]),
    ("R", "Programming Languages", True, []),
    ("Scala", "Programming Languages", True, []),

    # Web frameworks / backend
    ("Django", "Web Frameworks", True, []),
    ("Flask", "Web Frameworks", True, []),
    ("FastAPI", "Web Frameworks", True, []),
    ("React", "Web Frameworks", True, []),
    ("Node.js", "Web Frameworks", True, ["NodeJS", "Node"]),
    ("REST API", "Web Frameworks", True, ["RESTful API"]),
    ("GraphQL", "Web Frameworks", True, []),
    ("Microservices", "Web Frameworks", True, []),

    # Data & ML libraries
    ("Pandas", "Data & ML Libraries", True, []),
    ("NumPy", "Data & ML Libraries", True, []),
    ("Scikit-Learn", "Data & ML Libraries", True, ["sklearn"]),
    ("TensorFlow", "Data & ML Libraries", True, []),
    ("PyTorch", "Data & ML Libraries", True, []),
    ("XGBoost", "Data & ML Libraries", True, []),
    ("LightGBM", "Data & ML Libraries", True, []),
    ("Matplotlib", "Data & ML Libraries", True, []),
    ("Seaborn", "Data & ML Libraries", True, []),
    ("Plotly", "Data & ML Libraries", True, []),
    ("spaCy", "Data & ML Libraries", True, []),
    ("BERT", "Data & ML Libraries", True, []),
    ("Transformers", "Data & ML Libraries", True, []),

    # AI / ML concepts
    ("Machine Learning", "AI/ML Concepts", True, ["ML"]),
    ("Deep Learning", "AI/ML Concepts", True, ["DL"]),
    ("Natural Language Processing", "AI/ML Concepts", True, ["NLP"]),
    ("Computer Vision", "AI/ML Concepts", True, []),
    ("Reinforcement Learning", "AI/ML Concepts", True, []),
    ("Feature Engineering", "AI/ML Concepts", True, []),
    ("MLOps", "AI/ML Concepts", True, []),
    ("A/B Testing", "AI/ML Concepts", True, []),
    ("Bayesian Inference", "AI/ML Concepts", True, []),
    ("Statistics", "AI/ML Concepts", True, []),
    ("Recommendation Systems", "AI/ML Concepts", True, []),
    ("Fraud Detection", "AI/ML Concepts", True, []),
    ("Credit Risk", "AI/ML Concepts", True, []),
    ("Entity Resolution", "AI/ML Concepts", True, []),
    ("RAG", "AI/ML Concepts", True, ["Retrieval Augmented Generation"]),
    ("LLMs", "AI/ML Concepts", True, ["Large Language Models"]),
    ("GPT", "AI/ML Concepts", True, []),

    # Explainability
    ("SHAP", "Explainability", True, []),
    ("LIME", "Explainability", True, []),

    # Databases
    ("PostgreSQL", "Databases", True, ["Postgres"]),
    ("MySQL", "Databases", True, []),
    ("MongoDB", "Databases", True, []),
    ("Redis", "Databases", True, []),
    ("Elasticsearch", "Databases", True, []),

    # Cloud & DevOps
    ("AWS", "Cloud & DevOps", True, ["Amazon Web Services"]),
    ("GCP", "Cloud & DevOps", True, ["Google Cloud Platform", "Google Cloud"]),
    ("Azure", "Cloud & DevOps", True, ["Microsoft Azure"]),
    ("Docker", "Cloud & DevOps", True, []),
    ("Kubernetes", "Cloud & DevOps", True, ["K8s"]),
    ("Terraform", "Cloud & DevOps", True, []),
    ("Ansible", "Cloud & DevOps", True, []),
    ("Linux", "Cloud & DevOps", True, []),
    ("CI/CD", "Cloud & DevOps", True, ["Continuous Integration/Continuous Deployment"]),
    ("Git", "Cloud & DevOps", True, []),
    ("MLflow", "Cloud & DevOps", True, []),
    ("Airflow", "Cloud & DevOps", True, []),
    ("dbt", "Cloud & DevOps", True, []),

    # Data engineering
    ("Spark", "Data Engineering", True, ["Apache Spark"]),
    ("Kafka", "Data Engineering", True, ["Apache Kafka"]),
    ("Data Pipelines", "Data Engineering", True, []),
    ("ELT/ETL", "Data Engineering", True, ["ETL", "ELT"]),

    # BI & analytics tools
    ("Tableau", "BI & Analytics Tools", True, []),
    ("Power BI", "BI & Analytics Tools", True, ["PowerBI"]),
    ("Looker", "BI & Analytics Tools", True, []),
    ("Excel", "BI & Analytics Tools", True, ["Microsoft Excel", "MS Excel"]),
    ("PowerPoint", "BI & Analytics Tools", True, ["Microsoft PowerPoint", "MS PowerPoint"]),
    ("Data Analysis", "BI & Analytics Tools", True, []),

    # Business & soft skills
    ("Project Management", "Business & Soft Skills", False, []),
    ("Communication", "Business & Soft Skills", False, []),
    ("Leadership", "Business & Soft Skills", False, []),
    ("Agile", "Business & Soft Skills", False, []),
    ("Scrum", "Business & Soft Skills", False, []),
    ("Stakeholder Management", "Business & Soft Skills", False, []),
    ("Budgeting", "Business & Soft Skills", False, []),
    ("Sales", "Business & Soft Skills", False, []),
    ("Marketing", "Business & Soft Skills", False, []),
    ("Customer Service", "Business & Soft Skills", False, []),
    ("HR Management", "Business & Soft Skills", False, ["Human Resources Management"]),
    ("Financial Modelling", "Business & Soft Skills", False, ["Financial Modeling"]),
    ("Accounting", "Business & Soft Skills", False, []),
    ("Legal Research", "Business & Soft Skills", False, []),
    ("Clinical Research", "Business & Soft Skills", False, []),
    ("Public Speaking", "Business & Soft Skills", False, []),
    ("Negotiation", "Business & Soft Skills", False, []),
    ("Strategic Planning", "Business & Soft Skills", False, []),
]


class Command(BaseCommand):
    help = "Seed SkillTaxonomy with a consolidated skill vocabulary"

    def handle(self, *args, **options):
        from apps.taxonomy.models import SkillTaxonomy

        created, updated = 0, 0
        for canonical_name, category, is_technical, aliases in SKILLS:
            obj, was_created = SkillTaxonomy.objects.update_or_create(
                name=canonical_name.lower(),
                defaults={
                    "canonical_name": canonical_name,
                    "category": category,
                    "is_technical": is_technical,
                    "aliases": aliases,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created} skills created, {updated} updated. Total: {SkillTaxonomy.objects.count()}"
        ))
