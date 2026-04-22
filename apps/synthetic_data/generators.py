"""
Synthetic data generators using Faker.
Produces realistic candidates, jobs, applications, and recruiter decisions
across global regions — including configurable bias scenarios for fairness testing.
"""
import random
from dataclasses import dataclass, field
from typing import Optional

from faker import Faker

fake = Faker()

# ──────────────────────────────────────────────────────────────────────────────
# Reference data
# ──────────────────────────────────────────────────────────────────────────────

GLOBAL_COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France", "India",
    "Canada", "Australia", "Brazil", "Japan", "Singapore", "Netherlands",
    "Sweden", "Nigeria", "South Africa", "UAE", "Poland", "Spain", "Italy",
]

TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "django", "flask",
    "fastapi", "nodejs", "postgresql", "mysql", "mongodb", "redis", "docker",
    "kubernetes", "aws", "gcp", "azure", "machine learning", "nlp",
    "scikit-learn", "pytorch", "tensorflow", "sql", "git", "ci/cd",
    "spark", "kafka", "data analysis", "pandas", "numpy", "terraform",
    "ansible", "linux", "rest api", "graphql", "microservices",
]

NON_TECH_SKILLS = [
    "project management", "communication", "leadership", "agile", "scrum",
    "data analysis", "excel", "powerpoint", "stakeholder management",
    "budgeting", "sales", "marketing", "customer service", "hr management",
    "financial modelling", "accounting", "legal research", "clinical research",
    "public speaking", "negotiation", "strategic planning",
]

JOB_TITLES = [
    "Software Engineer", "Data Scientist", "ML Engineer", "Backend Developer",
    "Frontend Developer", "Full Stack Developer", "DevOps Engineer",
    "Product Manager", "UX Designer", "Data Analyst", "Data Engineer",
    "HR Manager", "Recruiter", "Marketing Manager", "Financial Analyst",
    "Project Manager", "Business Analyst", "Nurse", "Pharmacist",
    "Mechanical Engineer", "Civil Engineer", "Research Scientist",
]

INDUSTRIES = [
    "Technology", "Finance", "Healthcare", "Education", "Retail",
    "Manufacturing", "Energy", "Media", "Consulting", "Legal",
    "Logistics", "Real Estate", "Automotive", "Telecommunications",
]

EDUCATION_LEVELS = ["high_school", "associate", "bachelor", "master", "phd"]
SENIORITY_LEVELS = ["intern", "junior", "mid", "senior", "lead", "principal"]
GENDER_VALUES = ["male", "female", "non_binary", "prefer_not_to_say"]
AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"]
ETHNICITY_VALUES = [
    "White", "Black", "Asian", "Hispanic", "Middle Eastern",
    "Mixed", "Other", "Prefer not to say",
]

# ──────────────────────────────────────────────────────────────────────────────
# Bias scenario configuration
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BiasScenario:
    """
    Defines how recruiter shortlist probabilities differ across demographic groups.

    base_shortlist_rate : probability a candidate gets shortlisted with no bias
    group_multipliers   : per-group rate multiplier  (1.0 = no bias, 0.5 = half as likely)
    attribute           : which protected attribute this scenario targets
    name                : human-readable scenario label
    description         : what bias is being simulated

    Example — gender bias in tech hiring:
        base_shortlist_rate = 0.50
        group_multipliers   = {"male": 1.0, "female": 0.55, "non_binary": 0.50}
        → female candidates are shortlisted at 55% the rate of male candidates
        → DI ratio ≈ 0.55  (below 0.80 threshold → bias flag triggered)
    """
    name: str
    description: str
    attribute: str
    base_shortlist_rate: float
    group_multipliers: dict
    hire_from_shortlist_rate: float = 0.40
    interview_from_shortlist_rate: float = 0.60


# ── Scenario catalogue ────────────────────────────────────────────────────────

BIAS_SCENARIOS = {
    "no_bias": BiasScenario(
        name="No Bias (Control)",
        description="All groups have equal selection rates. Used as control group.",
        attribute="gender",
        base_shortlist_rate=0.48,
        group_multipliers={
            "male": 1.0, "female": 1.0, "non_binary": 1.0, "prefer_not_to_say": 1.0,
        },
    ),
    "gender_bias_tech": BiasScenario(
        name="Gender Bias — Technology Sector",
        description=(
            "Simulates systemic under-selection of women in tech roles. "
            "Female candidates shortlisted at ~55% the rate of male candidates. "
            "DI ratio ≈ 0.55, well below the 4/5 threshold."
        ),
        attribute="gender",
        base_shortlist_rate=0.50,
        group_multipliers={
            "male": 1.0, "female": 0.55, "non_binary": 0.52, "prefer_not_to_say": 0.90,
        },
    ),
    "age_bias_senior": BiasScenario(
        name="Age Bias — Older Workers Disadvantaged",
        description=(
            "Simulates age discrimination where candidates aged 45+ are significantly "
            "less likely to be shortlisted despite equivalent qualifications. "
            "DI ratio ≈ 0.58."
        ),
        attribute="age_range",
        base_shortlist_rate=0.50,
        group_multipliers={
            "18-24": 0.85, "25-34": 1.0, "35-44": 0.95, "45-54": 0.58, "55+": 0.52,
        },
    ),
    "ethnicity_bias": BiasScenario(
        name="Ethnicity Bias — Racial Disparity",
        description=(
            "Simulates racial bias in shortlisting. White candidates are selected "
            "at a significantly higher rate than Black and Hispanic candidates. "
            "DI ratio ≈ 0.62."
        ),
        attribute="ethnicity",
        base_shortlist_rate=0.50,
        group_multipliers={
            "White": 1.0, "Asian": 0.90, "Black": 0.62, "Hispanic": 0.65,
            "Middle Eastern": 0.70, "Mixed": 0.80, "Other": 0.75,
            "Prefer not to say": 0.85,
        },
    ),
    "disability_bias": BiasScenario(
        name="Disability Bias",
        description=(
            "Simulates discrimination against candidates who disclosed a disability. "
            "DI ratio ≈ 0.65."
        ),
        attribute="disability_status",
        base_shortlist_rate=0.50,
        group_multipliers={True: 0.65, False: 1.0, None: 0.90},
    ),
    "mild_gender_bias": BiasScenario(
        name="Mild Gender Bias (borderline)",
        description=(
            "Borderline case just below the 4/5 rule. Tests detector sensitivity. "
            "DI ratio ≈ 0.78."
        ),
        attribute="gender",
        base_shortlist_rate=0.50,
        group_multipliers={
            "male": 1.0, "female": 0.78, "non_binary": 0.80, "prefer_not_to_say": 0.95,
        },
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Candidate generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_candidate_data() -> dict:
    gender = random.choice(GENDER_VALUES)
    num_skills = random.randint(4, 14)
    skill_pool = TECH_SKILLS + NON_TECH_SKILLS
    skills = random.sample(skill_pool, min(num_skills, len(skill_pool)))
    years_exp = round(random.uniform(0, 20), 1)

    return {
        "full_name": fake.name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number()[:20],
        "country": random.choice(GLOBAL_COUNTRIES),
        "city": fake.city(),
        "region": fake.state(),
        "remote_preference": random.choice(["onsite", "remote", "hybrid", "flexible"]),
        "current_title": random.choice(JOB_TITLES),
        "years_of_experience": years_exp,
        "seniority_level": random.choice(SENIORITY_LEVELS),
        "summary": fake.paragraph(nb_sentences=4),
        "highest_education": random.choice(EDUCATION_LEVELS),
        "education_field": random.choice([
            "Computer Science", "Engineering", "Business",
            "Science", "Arts", "Medicine",
        ]),
        "availability_status": random.choice(["actively_looking", "open", "not_looking"]),
        "expected_salary_min": random.randint(30000, 80000),
        "expected_salary_max": random.randint(80000, 200000),
        "salary_currency": "USD",
        "gender": gender,
        "age_range": random.choice(AGE_RANGES),
        "ethnicity": random.choice(ETHNICITY_VALUES),
        "disability_status": random.choice([True, False, None]),
        "is_synthetic": True,
        "raw_cv_text": fake.paragraph(nb_sentences=20),
        "skills": skills,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Job generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_job_data() -> dict:
    num_skills = random.randint(3, 10)
    skills = random.sample(TECH_SKILLS + NON_TECH_SKILLS, num_skills)
    return {
        "title": random.choice(JOB_TITLES),
        "company": fake.company(),
        "description": fake.paragraph(nb_sentences=8),
        "requirements": fake.paragraph(nb_sentences=5),
        "responsibilities": fake.paragraph(nb_sentences=5),
        "country": random.choice(GLOBAL_COUNTRIES),
        "city": fake.city(),
        "region": fake.state(),
        "work_model": random.choice(["onsite", "remote", "hybrid"]),
        "industry": random.choice(INDUSTRIES),
        "employment_type": random.choice(["full_time", "part_time", "contract"]),
        "experience_level": random.choice(["entry", "mid", "senior", "lead"]),
        "salary_min": random.randint(40000, 80000),
        "salary_max": random.randint(80000, 200000),
        "salary_currency": "USD",
        "status": "active",
        "source": "synthetic",
        "is_synthetic": True,
        "skills": skills,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Recruiter decision simulator
# ──────────────────────────────────────────────────────────────────────────────

def _compute_merit_probability(candidate, job_required_skills: list[str]) -> float:
    """
    Base shortlist probability derived from candidate merit (skills + experience).
    Range: 0.10 – 0.90, independent of demographics.
    """
    candidate_skills = set(
        s.lower() for s in candidate.skills.values_list("skill_name", flat=True)
    )
    job_skills = set(s.lower() for s in job_required_skills)

    skill_match = len(candidate_skills & job_skills) / max(len(job_skills), 1)
    exp_factor = min(candidate.years_of_experience / 10.0, 1.0)

    edu_weight = {
        "high_school": 0.1, "associate": 0.2, "bachelor": 0.5,
        "master": 0.7, "phd": 0.8,
    }.get(candidate.highest_education or "bachelor", 0.5)

    merit = (0.50 * skill_match) + (0.30 * exp_factor) + (0.20 * edu_weight)
    return max(0.10, min(merit, 0.90))


def simulate_recruiter_decision(
    candidate,
    job,
    scenario: BiasScenario,
    noise: float = 0.05,
) -> dict:
    """
    Simulate a recruiter's shortlist/interview/hire decision for one candidate–job pair.

    The decision is a combination of:
      - Merit probability (skills, experience, education)
      - Bias multiplier from the scenario (demographic adjustment)
      - Random noise (simulates human inconsistency)

    Returns a dict with shortlisted, interviewed, hired, and rejection_reason fields.
    """
    job_skills = list(job.skill_requirements.values_list("skill_name", flat=True))
    merit_prob = _compute_merit_probability(candidate, job_skills)

    # Apply demographic bias multiplier
    attr_value = getattr(candidate, scenario.attribute, None)
    bias_multiplier = scenario.group_multipliers.get(attr_value, 1.0)
    adjusted_prob = merit_prob * bias_multiplier * scenario.base_shortlist_rate / 0.50

    # Add noise
    adjusted_prob = max(0.0, min(adjusted_prob + random.gauss(0, noise), 1.0))

    shortlisted = random.random() < adjusted_prob
    interviewed = shortlisted and random.random() < scenario.interview_from_shortlist_rate
    hired = interviewed and random.random() < scenario.hire_from_shortlist_rate

    # Determine status
    if hired:
        status = "hired"
    elif interviewed:
        status = "interview"
    elif shortlisted:
        status = "shortlisted"
    else:
        status = "rejected"

    rejection_reason = ""
    if not shortlisted:
        possible_reasons = [
            "Insufficient experience",
            "Missing required skills",
            "Overqualified for role",
            "Position filled internally",
            "Salary expectations mismatch",
        ]
        rejection_reason = random.choice(possible_reasons)

    return {
        "status": status,
        "shortlisted": shortlisted,
        "interviewed": interviewed,
        "hired": hired,
        "merit_score": round(merit_prob, 4),
        "adjusted_score": round(adjusted_prob, 4),
        "bias_multiplier": round(bias_multiplier, 4),
        "rejection_reason": rejection_reason,
        "scenario_name": scenario.name,
        "is_synthetic": True,
    }


def generate_application_batch(
    candidates: list,
    jobs: list,
    scenario_key: str = "no_bias",
    applications_per_candidate: int = 3,
) -> list[dict]:
    """
    Generate a batch of applications with simulated recruiter decisions.

    Each candidate applies to `applications_per_candidate` randomly chosen jobs.
    Decisions are made according to the specified bias scenario.

    Returns a list of application dicts ready for bulk_create.
    """
    scenario = BIAS_SCENARIOS.get(scenario_key, BIAS_SCENARIOS["no_bias"])
    applications = []

    for candidate in candidates:
        selected_jobs = random.sample(jobs, min(applications_per_candidate, len(jobs)))
        for job in selected_jobs:
            decision = simulate_recruiter_decision(candidate, job, scenario)
            applications.append({
                "candidate": candidate,
                "job": job,
                "status": decision["status"],
                "recruiter_notes": (
                    f"[Synthetic | Scenario: {decision['scenario_name']}] "
                    f"Merit: {decision['merit_score']:.2f} | "
                    f"Bias multiplier: {decision['bias_multiplier']:.2f}"
                    + (f" | {decision['rejection_reason']}" if decision["rejection_reason"] else "")
                ),
                "is_synthetic": True,
            })

    return applications
