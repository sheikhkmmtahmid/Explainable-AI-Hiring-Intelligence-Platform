---
title: HiringAI Platform
emoji: 💼
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Explainable AI Hiring Intelligence Platform

**An Explainable and Fair NLP-Based Candidate–Job Matching Framework Using Django and Multi-Source Recruitment Data**

> Made by [SKMMT](https://skmmt.rootexception.com/)

---

## Overview

The Explainable AI Hiring Intelligence Platform is a production-grade Django web application that acts as an AI-powered decision-support system for recruitment. It is not a traditional ATS or a keyword matcher — it is a full hiring intelligence platform that helps recruiters justify decisions, understand why candidates are selected or rejected, and detect bias in hiring pipelines.

The system integrates live job APIs, synthetic recruitment data, semantic NLP matching via Sentence-BERT, explainable AI outputs via SHAP and LIME, and fairness analytics across protected demographic groups — all exposed through a clean REST API.

---

## Key Features

### Candidate–Job Matching
- Semantic matching using Sentence-BERT (SBERT) embeddings
- Hybrid scoring: semantic similarity + skill overlap + experience match + education match
- Batch matching across all candidates for a given job
- Ranked shortlists with configurable top-N output

### Explainable AI
- SHAP-based feature importance per match result
- LIME-based local explanation as an alternative method
- Human-readable summary: why a candidate matched, what skills are missing, what drove the score
- All outputs stored and served via REST API

### Fairness Analytics
- Disparate Impact Ratio (4/5 rule) per protected attribute
- Demographic Parity Difference across subgroups
- Supported attributes: gender, age range, ethnicity, disability status
- Bias flag raised automatically when DI ratio falls below 0.8

### Multi-Source Data Pipeline
- Live job ingestion from Adzuna API (Jooble and The Muse ready)
- Synthetic candidate and job generation (5000+ candidates, 1000+ jobs) using Faker
- CV upload and async parsing (PDF, DOCX, TXT)
- Skill ontology based on ESCO/O*NET patterns

### Recruiter Workflow
- Full application pipeline: Applied → Screening → Shortlisted → Interview → Offer → Hired/Rejected
- Recruiter notes and interview scheduling per application
- Pipeline snapshot analytics per job

### Global Support
- No UK-only assumptions — supports any country, city, region
- Remote / hybrid / on-site work model tracking
- Multi-currency salary fields
- Diverse synthetic data across 18+ global regions

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.2 + Django REST Framework |
| Authentication | JWT via djangorestframework-simplejwt |
| Database | PostgreSQL 15 |
| Cache / Message Broker | Redis 7 |
| Async Task Queue | Celery 5 + Celery Beat |
| NLP Embeddings | Sentence-BERT (all-MiniLM-L6-v2) |
| NLP Parsing | spaCy (en_core_web_sm) |
| Explainability | SHAP + LIME |
| Synthetic Data | Faker |
| Containerisation | Docker + Docker Compose |
| Python Version | 3.11 |

---

## Project Structure

```
Explainable AI Hiring Intelligence Platform/
│
├── config/                         # Django project configuration
│   ├── settings/
│   │   ├── base.py                 # Shared settings
│   │   ├── development.py          # Dev overrides
│   │   └── production.py           # Production overrides (S3, Sentry, HTTPS)
│   ├── urls.py                     # Root URL configuration
│   ├── celery.py                   # Celery application
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                           # Django applications (12 modules)
│   ├── accounts/                   # Custom user model, JWT auth, roles
│   ├── candidates/                 # Candidate profiles, CVs, skills, experience, embeddings
│   ├── jobs/                       # Job posts, skill requirements, embeddings
│   ├── applications/               # Application pipeline, notes, interview slots
│   ├── parsing/                    # CV text extraction and async parse jobs
│   ├── matching/                   # SBERT + hybrid scoring, batch matching
│   ├── explainability/             # SHAP/LIME explanation reports
│   ├── fairness/                   # Bias detection, subgroup metrics
│   ├── ingestion/                  # External API ingestion (Adzuna, Jooble)
│   ├── synthetic_data/             # Faker-based data generators and tasks
│   ├── taxonomy/                   # Skill ontology, job role templates
│   └── analytics/                  # Platform summary, pipeline snapshots
│
├── ml/                             # Machine learning layer
│   ├── embeddings/
│   │   └── encoder.py              # Thread-safe lazy-loaded SBERT singleton
│   ├── matching/
│   │   └── scorer.py               # 7-feature vector builder
│   ├── explainability/
│   │   ├── shap_explainer.py       # SHAP feature importance
│   │   └── lime_explainer.py       # LIME local explanations
│   └── fairness/
│       └── metrics.py              # DI ratio, demographic parity, equal opportunity
│
├── templates/                      # Django HTML templates
├── static/                         # Static CSS/JS assets
├── media/                          # User-uploaded files (CVs, etc.)
│
├── requirements/
│   ├── base.txt                    # Core dependencies
│   ├── development.txt             # Dev + testing tools
│   └── production.txt              # Production server + monitoring
│
├── .venv/                          # Python virtual environment (local)
├── .env                            # Local environment variables (not committed)
├── .env.example                    # Template for environment variables
├── Dockerfile                      # Production Docker image
├── docker-compose.yml              # Full local stack (DB + Redis + Web + Celery)
├── manage.py                       # Django management entry point
├── pyproject.toml                  # Black, isort, ruff, pytest configuration
└── README.md
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

| Endpoint | Description |
|---|---|
| `POST /auth/register/` | Register a new user |
| `POST /auth/login/` | Login and receive JWT tokens |
| `POST /auth/token/refresh/` | Refresh access token |
| `GET/PUT /auth/me/` | View and update own profile |
| `GET/POST /candidates/` | List candidates or create a profile |
| `POST /candidates/{id}/upload_cv/` | Upload a CV (triggers async parsing) |
| `GET /parsing/status/{cv_id}/` | Check CV parse job status |
| `GET/POST /jobs/` | List jobs or create a job post |
| `GET /jobs/active/` | List all active job posts |
| `GET/POST /applications/` | List or create applications |
| `PATCH /applications/{id}/update_status/` | Move application through pipeline |
| `POST /applications/{id}/schedule_interview/` | Schedule an interview slot |
| `POST /matching/trigger/{job_id}/` | Trigger batch matching for a job (async) |
| `GET /matching/results/?job={id}` | Get match results for a job |
| `GET /matching/top-candidates/{job_id}/` | Get top-N ranked candidates |
| `GET/POST /explainability/{match_result_id}/` | Get or generate explanation |
| `GET/POST /fairness/{job_id}/` | Get or compute fairness report |
| `POST /ingestion/trigger/` | Trigger live job ingestion from an API |
| `GET /ingestion/runs/` | View ingestion run history |
| `POST /synthetic/generate/` | Generate synthetic candidates or jobs |
| `GET /synthetic/runs/` | View synthetic generation history |
| `GET /taxonomy/skills/` | Browse skill ontology |
| `GET /analytics/summary/` | Platform-wide statistics |
| `GET /analytics/pipeline/{job_id}/` | Pipeline funnel for a specific job |

---

## User Roles

| Role | Access |
|---|---|
| `admin` | Full platform access |
| `recruiter` | All candidates, jobs, applications, matching, fairness |
| `analyst` | Read-only access to matching, fairness, analytics |
| `candidate` | Own profile and own applications only |

---

## Matching Score Breakdown

Each candidate–job match produces five component scores combined into one overall score:

| Component | Weight | Description |
|---|---|---|
| Semantic similarity | 50% | Cosine similarity between SBERT embeddings of candidate profile and job description |
| Skill overlap | 30% | Ratio of required job skills present in candidate's skill set |
| Experience match | 15% | Candidate years of experience vs. job requirement |
| Education match | 5% | Ordinal comparison of education levels |

---

## Explainability Output Example

```json
{
  "method": "shap",
  "feature_importances": {
    "semantic_similarity": 0.72,
    "skill_overlap": 0.65,
    "experience_match": 0.80,
    "education_match": 1.0
  },
  "top_positive_factors": [
    { "feature": "skill:python", "impact": 0.05, "direction": "positive" },
    { "feature": "semantic_profile_match", "impact": 0.72, "direction": "positive" }
  ],
  "top_negative_factors": [
    { "feature": "missing_skill:kubernetes", "impact": -0.05, "direction": "negative" }
  ],
  "missing_skills": ["kubernetes", "terraform"],
  "summary_text": "Overall match score: 73.4%. The candidate matches 7 required skills. Missing 2 required skills: kubernetes, terraform. Experience score: 80.0% | Semantic profile alignment: 72.0%."
}
```

---

## Fairness Report Example

```json
{
  "protected_attribute": "gender",
  "disparate_impact_ratio": 0.76,
  "selection_rate_overall": 0.42,
  "bias_flag": true,
  "subgroups": {
    "male":   { "total": 210, "shortlisted": 102, "selection_rate": 0.486 },
    "female": { "total": 198, "shortlisted":  74, "selection_rate": 0.374 },
    "non_binary": { "total": 42, "shortlisted": 16, "selection_rate": 0.381 }
  }
}
```

A `bias_flag: true` means the Disparate Impact Ratio is below 0.8 (the 4/5 rule), indicating potential systemic bias.

---

## Running the Platform (Quick Start)

Once everything is installed, you need **4 terminals open simultaneously** every time you run the platform.

### Terminal 1 — Redis (run once; skip if already running)
```powershell
docker run -d -p 6379:6379 --name redis redis:7-alpine
```
> If it says "name already in use", Redis is already running — skip this step.

### Terminal 2 — Celery Worker (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform"
.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo
```

### Terminal 3 — Django Backend (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform"
.venv\Scripts\Activate.ps1
python manage.py runserver
```

### Terminal 4 — React Frontend (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform\frontend"
npm install
npm run dev
```
> `npm install` only needed the first time.

Once all 4 are running:

| Interface | URL |
|---|---|
| **HR Frontend (React)** | `http://localhost:3000` |
| **Backend API** | `http://127.0.0.1:8000/api/v1/` |
| **Django Admin** | `http://127.0.0.1:8000/admin/` |

Login with the superuser account you created during setup.

---

## How to Run

### Option 1 — Local Development (Recommended for development)

**Prerequisites:** Python 3.11, PostgreSQL 15, Redis 7

**Step 1 — Clone and enter the project**
```bash
cd "Explainable AI Hiring Intelligence Platform"
```

**Step 2 — Activate the virtual environment**
```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**Step 3 — Copy environment variables**
```bash
cp .env.example .env
# Edit .env and fill in DB credentials and any API keys you have
```

**Step 4 — Create the database**
```bash
# In psql or pgAdmin:
CREATE USER hiringai WITH PASSWORD 'hiringai_pass';
CREATE DATABASE hiringai_db OWNER hiringai;
```

**Step 5 — Run migrations**
```bash
python manage.py migrate
```

**Step 6 — Create a superuser**
```bash
python manage.py createsuperuser
```

**Step 7 — Download the spaCy model**
```bash
python -m spacy download en_core_web_sm
```

**Step 8 — Start the development server**
```bash
python manage.py runserver
```

**Step 9 — Start Celery worker (in a separate terminal)**
```bash
celery -A config.celery worker --loglevel=info
```

**Step 10 — Start Celery Beat scheduler (in a separate terminal)**
```bash
celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

The API will be available at `http://localhost:8000/api/v1/`
The admin panel will be available at `http://localhost:8000/admin/`

---

### Option 2 — Docker Compose (Full stack in one command)

**Prerequisites:** Docker Desktop

```bash
# Copy environment file
cp .env.example .env

# Build and start all services
docker-compose up --build

# In a separate terminal, run migrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py loaddata initial_taxonomy  # optional
```

This starts:
- `db` — PostgreSQL 15
- `redis` — Redis 7
- `web` — Django development server on port 8000
- `celery_worker` — Celery worker (4 concurrent processes)
- `celery_beat` — Celery Beat periodic task scheduler

---

### Generating Synthetic Data

Once the server is running, seed the platform with synthetic data via the API:

```bash
# Generate 500 synthetic candidates
curl -X POST http://localhost:8000/api/v1/synthetic/generate/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"kind": "candidates", "count": 500}'

# Generate 200 synthetic jobs
curl -X POST http://localhost:8000/api/v1/synthetic/generate/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"kind": "jobs", "count": 200}'
```

---

### Ingesting Live Jobs from Adzuna

Add your Adzuna credentials to `.env`, then:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/trigger/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"source": "adzuna", "query": "data scientist", "country": "us", "location": "New York"}'
```

---

### Running Tests

```bash
pytest
pytest --cov=apps --cov-report=html   # with coverage report
```

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | — (required) |
| `DJANGO_DEBUG` | Enable debug mode | `True` |
| `DJANGO_SETTINGS_MODULE` | Settings module path | `config.settings.development` |
| `DB_NAME` | PostgreSQL database name | `hiringai_db` |
| `DB_USER` | PostgreSQL username | `hiringai` |
| `DB_PASSWORD` | PostgreSQL password | `hiringai_pass` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis cache URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/2` |
| `ADZUNA_APP_ID` | Adzuna API app ID | — |
| `ADZUNA_API_KEY` | Adzuna API key | — |
| `SBERT_MODEL_NAME` | Sentence-BERT model | `all-MiniLM-L6-v2` |
| `SPACY_MODEL_NAME` | spaCy model | `en_core_web_sm` |

---

## Data Sources

| Source | Type | Usage |
|---|---|---|
| Adzuna API | Live | Real job listings (global) |
| Jooble API | Live | Additional job listings (ready to integrate) |
| The Muse API | Live | Additional job listings (ready to integrate) |
| Faker (synthetic) | Generated | Diverse candidates and jobs for simulation |
| Kaggle datasets | Offline | Resume and job datasets for training/evaluation |
| ESCO / O\*NET | Reference | Skill ontology and taxonomy |

> LinkedIn and Indeed are intentionally excluded — scraping these platforms violates their terms of service.

---

## Design Principles

- **Explainability first:** Every match score has a human-readable explanation. No black-box outputs.
- **Fairness by design:** Protected attributes are stored separately from matching logic, analysed post-hoc to detect systemic bias.
- **Global applicability:** No hard-coded country or region assumptions. All location fields are free-form strings.
- **Service layer architecture:** Business logic lives in `services.py` files, not in views or models.
- **Async ML tasks:** All embedding generation and batch matching runs as Celery tasks, keeping the API non-blocking.
- **Modular apps:** Each of the 12 apps has a single responsibility and can be extended independently.

---

## Academic Context

This project demonstrates:

- NLP-based semantic matching using transformer embeddings (SBERT)
- Explainable AI using SHAP and LIME for hiring decision transparency
- Algorithmic fairness analysis with Disparate Impact and Demographic Parity metrics
- Multi-source data integration (APIs + synthetic + ontology)
- Production-ready Django architecture with async processing

It serves as both a portfolio project and a research prototype for the academic paper:

> *"An Explainable and Fair NLP-Based Candidate–Job Matching Framework Using Django and Multi-Source Recruitment Data"*

---

## License

This project is for academic and portfolio purposes.
