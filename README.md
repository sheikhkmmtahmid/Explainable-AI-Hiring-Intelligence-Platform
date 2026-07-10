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

**An Explainable and Fair NLP-Based Candidate to Job Matching Framework Using Django and Multi-Source Recruitment Data**

> Made by [SKMMT](https://skmmt.rootexception.com/).
> View [Demo](https://sheikhkmmtahmid-hiringai-platform.hf.space/) · [About & data sources](https://sheikhkmmtahmid-hiringai-platform.hf.space/about) · [Governance](https://sheikhkmmtahmid-hiringai-platform.hf.space/governance)

---

## Overview

The Explainable AI Hiring Intelligence Platform is a production-grade Django + React application that acts as an AI-powered decision-support system for recruitment. It is not a traditional ATS or a keyword matcher; it is a full hiring intelligence platform that helps recruiters justify decisions, understand why candidates are selected or rejected, and audit hiring pipelines for bias.

The system runs semantic NLP matching via Sentence-BERT, explainable AI outputs via SHAP and LIME, and fairness analytics across protected demographic groups, all exposed through a multi-tenant REST API with its own billing layer. It runs against a mix of real recruitment data pulled from eight public datasets and synthetic data generated specifically to exercise the fairness-audit features under known, controlled bias scenarios. The two are never blended silently: every job and candidate record is tagged with where it came from, and the [About page](https://sheikhkmmtahmid-hiringai-platform.hf.space/about) documents exactly what was imported, from where, under what license, and what its limitations are.

---

## Key Features

### Candidate to Job Matching
- Semantic matching using Sentence-BERT (SBERT) embeddings
- Hybrid scoring: semantic similarity, skill overlap, experience match, and education match, combined by a trained GradientBoostingClassifier (falls back to fixed, principled weights until an organization has enough real hiring decisions to learn from responsibly)
- Batch matching across the full candidate pool for a given job, run async via Celery
- Ranked shortlists with configurable top-N output, plus a matching confidence tier (no data, early signal, or calibrated) based on how many real decisions exist for that job

### Explainable AI
- SHAP-based feature importance per match result
- LIME-based local explanation as an alternative method
- Human-readable summary of why a candidate matched, what skills are missing, and what drove the score
- All outputs stored and served via REST API

### Fairness Analytics
- Disparate Impact Ratio (4/5 rule) and Demographic Parity Difference per protected attribute (gender, age range, ethnicity, disability status)
- Audits real recruiter decisions (shortlisted, interviewed, offered, hired, rejected) once they exist; falls back to a clearly labeled provisional estimate from the AI's own ranking when they don't, and never mixes the two silently
- Recruiter override tracking: how often a real decision went against what the AI ranking would have suggested
- Benchmark comparison against real 2018 EEOC EEO-1 national workforce data
- A counterfactual name-bias probe that swaps first names across race and gender coded variants of the same resume, holding everything else fixed, to check whether the match score is sensitive to a name alone

### Real-World and Synthetic Data Pipeline
- Over 38,500 real job postings and 13,000 real candidate profiles imported from eight public datasets (see below), deduplicated by content hash both within and across sources
- The one dataset with real hiring outcomes, a 2004 audit study on racial discrimination in callbacks, is imported with its actual 4,870 real application decisions and 392 real callbacks intact
- Synthetic candidate and job generation using Faker, purpose-built to model protected attributes explicitly so the fairness features have something realistic to test against
- CV upload and async parsing (PDF, DOCX, TXT) via the same spaCy-based extraction pipeline used for every imported real resume
- Skill ontology synced from ESCO, with a moderation queue for skills proposed during CV parsing or job creation that don't already exist in the taxonomy

### Multi-Tenancy & Billing
- Each organization's candidates, jobs, applications, and fairness data are isolated from every other organization's
- Platform staff accounts can see and manage across every organization; recruiter and analyst accounts are scoped to their own
- Open-ended, pluggable billing: payment providers (Stripe, SSLCommerz) are rows in a database table seeded by a management command, not a hardcoded enum, so adding a new payment rail for a new country doesn't require a rewrite of the billing flow
- Manual payment proof review path for providers that aren't fully automated, with an admin review queue

### Recruiter Workflow
- Full application pipeline: Applied, Screening, Shortlisted, Interview, Offer, Hired or Rejected
- Recruiter notes and interview scheduling per application
- Lightweight task management for recruiter to-dos tied to a job or candidate
- Pipeline snapshot analytics per job

### Global Support
- No country-specific assumptions; supports any country, city, or region
- Remote, hybrid, or on-site work model tracking
- Multi-currency salary fields
- Real data spans dozens of countries; synthetic data is generated across 18+ global regions

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.2 + Django REST Framework |
| Frontend | React 18 + Vite |
| Authentication | JWT via djangorestframework-simplejwt, with server-side token blacklisting on logout |
| Database | TiDB Cloud (MySQL-compatible, serverless) via PyMySQL |
| Cache / Message Broker | Redis 7 |
| Async Task Queue | Celery 5 + Celery Beat |
| NLP Embeddings | Sentence-BERT (all-MiniLM-L6-v2) |
| NLP Parsing | spaCy (en_core_web_sm) |
| Match Scoring | GradientBoostingClassifier (scikit-learn) over 4 hand-engineered features |
| Explainability | SHAP + LIME |
| Synthetic Data | Faker |
| Billing | Stripe + SSLCommerz, pluggable provider model |
| Containerisation | Docker (single-image build serving API and built React frontend) |
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
│   │   └── huggingface.py          # Container deployment settings (JSON logging, static file serving)
│   ├── urls.py                     # Root URL configuration
│   ├── health.py                   # /healthz/ liveness check (DB + cache)
│   ├── logging_formatters.py       # Structured JSON log formatter for deployed environments
│   ├── celery.py                   # Celery application
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                           # Django applications (15 feature modules)
│   ├── accounts/                   # Custom user model, JWT auth, roles, org membership
│   ├── organizations/              # Multi-tenancy: the Organization model and boundary
│   ├── candidates/                 # Candidate profiles, CVs, skills, experience, embeddings
│   ├── jobs/                       # Job posts, skill requirements, embeddings
│   ├── applications/               # Application pipeline, notes, interview slots, override tracking
│   ├── parsing/                    # CV text extraction and async parse jobs
│   ├── matching/                   # SBERT + hybrid scoring, batch matching, confidence tiers
│   ├── explainability/             # SHAP/LIME explanation reports
│   ├── fairness/                   # Bias detection, subgroup metrics, EEOC benchmark, override summary
│   ├── ingestion/                  # Real dataset importers (8 sources) plus live job API ingestion
│   ├── synthetic_data/             # Faker-based data generators and tasks
│   ├── taxonomy/                   # ESCO-synced skill ontology and moderation queue
│   ├── analytics/                  # Platform summary, pipeline snapshots
│   ├── billing/                    # Plans, subscriptions, pluggable payment providers
│   ├── tasks/                      # Lightweight recruiter task management
│   └── common/                     # Shared pagination, lorem-style text helpers
│
├── ml/                              # Machine learning layer
│   ├── embeddings/
│   │   └── encoder.py               # Thread-safe lazy-loaded SBERT singleton
│   ├── matching/
│   │   ├── scorer.py                # 4-feature vector builder
│   │   └── trainer.py               # GradientBoostingClassifier training on real decisions
│   ├── explainability/
│   │   ├── shap_explainer.py        # SHAP feature importance
│   │   └── lime_explainer.py        # LIME local explanations
│   └── fairness/
│       ├── metrics.py               # DI ratio, demographic parity, equal opportunity
│       ├── eeoc_benchmarks.py       # Real EEOC 2018 EEO-1 national workforce comparison
│       └── name_bias_probe.py       # Counterfactual name-swap sensitivity test
│
├── frontend/                        # React 18 + Vite single-page app
│   └── src/
│       ├── pages/                   # Route-level views, including the public About and Governance pages
│       ├── api/                     # Axios client and one module per backend resource
│       └── components/
│
├── templates/                      # Django HTML templates (serves the built React index.html)
├── static/                         # Static CSS/JS assets
├── media/                          # User-uploaded files (CVs, etc.)
├── docs/                           # Monitoring/alerting notes, payment go-live checklist
├── scripts/                        # Load testing and one-off operational scripts
│
├── requirements/
│   ├── base.txt                    # Core dependencies
│   ├── development.txt             # Dev + testing tools
│   └── production.txt              # Production server + monitoring
│
├── .venv/                          # Python virtual environment (local)
├── .env                            # Local environment variables (not committed)
├── .env.example                    # Template for environment variables
├── Dockerfile                      # Single-image build: React build + Django, served by Gunicorn
├── start.sh                        # Container entrypoint: migrate, collectstatic, Celery + Gunicorn
├── manage.py                       # Django management entry point
├── pyproject.toml                  # Black, isort, ruff, pytest configuration
└── README.md
```

Two of the entries under `apps/` don't show up in that feature list on purpose. `celery_beat_migrations` and `token_blacklist_migrations` are migration-only packages for `django-celery-beat` and `simplejwt`'s token blacklist app. TiDB rejects some of the ALTER TABLE patterns their upstream migrations generate, so those migrations are faked and replaced with TiDB-compatible SQL via a management command instead.

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`. `GET /healthz/` (unprefixed) is a liveness check for deployment monitoring.

| Endpoint | Description |
|---|---|
| `POST /auth/register/` | Register a new user |
| `POST /auth/login/` | Login and receive JWT tokens |
| `POST /auth/token/refresh/` | Refresh access token |
| `POST /auth/logout/` | Blacklist the refresh token server-side |
| `GET/PUT /auth/me/` | View and update own profile |
| `GET /organizations/me/` | View own organization |
| `GET/POST /candidates/` | List candidates or create a profile |
| `POST /candidates/{id}/upload_cv/` | Upload a CV (triggers async parsing) |
| `GET /parsing/status/{cv_id}/` | Check CV parse job status |
| `GET/POST /jobs/` | List jobs or create a job post (supports search, source/status filters, pagination) |
| `GET /jobs/active/` | List all active job posts |
| `GET/POST /applications/` | List or create applications |
| `PATCH /applications/{id}/update_status/` | Move application through pipeline |
| `POST /applications/{id}/schedule_interview/` | Schedule an interview slot |
| `POST /matching/trigger/{job_id}/` | Trigger batch matching for a job (async) |
| `GET /matching/results/?job={id}` | Get match results for a job |
| `GET /matching/top-candidates/{job_id}/` | Get top-N ranked candidates |
| `GET /matching/confidence/?job_id={id}` | Matching confidence tier for a job |
| `GET/POST /explainability/{match_result_id}/` | Get or generate explanation |
| `GET/POST /fairness/{job_id}/` | Get or compute fairness report |
| `GET /fairness/overrides/?job_id={id}` | Recruiter override rate vs AI ranking |
| `POST /ingestion/trigger/` | Trigger live job ingestion from an API |
| `GET /ingestion/runs/` | View ingestion run history |
| `POST /synthetic/generate/` | Generate synthetic candidates or jobs |
| `GET /synthetic/runs/` | View synthetic generation history |
| `GET /taxonomy/skills/` | Browse or search the skill ontology |
| `GET /analytics/summary/` | Platform-wide statistics |
| `GET /analytics/pipeline/{job_id}/` | Pipeline funnel for a specific job |
| `GET /billing/plans/`, `GET /billing/providers/` | Available plans and payment providers |
| `GET/POST /billing/subscription/`, `/billing/subscribe/` | View or change an organization's subscription |
| `GET/POST /tasks/` | Recruiter task management |

---

## User Roles & Multi-Tenancy

| Role | Access |
|---|---|
| `admin` (platform staff) | Full access across every organization |
| `recruiter` | All candidates, jobs, applications, matching, fairness, billing, scoped to their own organization |
| `analyst` | Read-only access to matching, fairness, analytics, scoped to their own organization |
| `candidate` | Own profile and own applications only |

Every recruiter and analyst account belongs to exactly one `Organization`. Candidates, jobs, applications, match results, and fairness reports are all scoped to that boundary, so one organization never sees another's data. The public job board (`GET /jobs/`, `/jobs/active/`) is the one deliberate exception: active job postings from every organization are visible to anyone, the same as any real job board.

---

## Matching Score Breakdown

Each candidate to job match produces four component scores combined into one overall score by the trained GradientBoostingClassifier:

| Component | Default Weight | Description |
|---|---|---|
| Semantic similarity | 50% | Cosine similarity between SBERT embeddings of candidate profile and job description |
| Skill overlap | 30% | Ratio of required job skills present in candidate's skill set |
| Experience match | 15% | Candidate years of experience vs. the job's actual stated requirement |
| Education match | 5% | Ordinal comparison against the job's actual stated education requirement, not an assumed default |

These are the fixed weights the platform falls back to until an organization has enough real hiring decisions logged to train the classifier on its own outcomes responsibly. Once it does, `ml/matching/trainer.py` retrains against that organization's real `hired`/`rejected` labels instead.

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
  "basis": "real_decisions",
  "disparate_impact_ratio": 0.76,
  "demographic_parity_difference": 0.11,
  "bias_detected": true,
  "subgroups": {
    "male":   { "total": 210, "selected": 102, "selection_rate": 0.486 },
    "female": { "total": 198, "selected":  74, "selection_rate": 0.374 },
    "non_binary": { "total": 42, "selected": 16, "selection_rate": 0.381 }
  },
  "eeoc_benchmark": {
    "supported": true,
    "source_year": 2018,
    "note": "Compared against real EEOC EEO-1 national workforce data"
  }
}
```

`"basis": "real_decisions"` means this report audits actual recruiter decisions. If a job has no shortlisted, interviewed, hired, or rejected decisions yet, `basis` is `"ai_rank_provisional"` instead, and the report is computed from the AI's ranking alone until real decisions exist. A `bias_detected: true` flag means the Disparate Impact Ratio fell below 0.8 (the 4/5 rule).

---

## Why These Models

Each of the four models in this stack was picked for a specific reason, and each had real alternatives that were considered and not used. This section documents that, so the choices read as deliberate rather than arbitrary.

**SBERT (all-MiniLM-L6-v2)** needs to embed a growing pool of tens of thousands of resumes and jobs on a small, self-hosted server with no GPU, so speed matters as much as raw quality. Alternatives considered:
- `all-mpnet-base-v2`, a stronger sibling in the same sentence-transformers family, scores higher on general benchmarks but runs about 5x slower.
- [TechWolf/JobBERT-v2](https://huggingface.co/TechWolf/JobBERT-v2), public, English, MIT licensed, trained on 5.5M+ real US job ads. Not used because it is built to match short job titles against skill lists (64-token practical limit), not full job descriptions or resumes.
- [CareerBERT](https://huggingface.co/lwolfrum2/careerbert-g), a model fine-tuned specifically to match resumes to ESCO job categories, exactly the right concept, and its own paper reports it beating generic baselines. Not used because it is trained on German text (`deepset/gbert-base`), not English.
- conSultantBERT (Randstad, [paper](https://arxiv.org/abs/2109.06501)), trained on 270,000 real resume-vacancy pairs and reported to outperform generic SBERT baselines. Not used because it was never released publicly, no weights, no code.

**spaCy (en_core_web_sm)** parses resumes asynchronously, sometimes in batches, so throughput matters. Alternatives considered:
- Flair and Stanford's Stanza report slightly higher accuracy on standard NER benchmarks, but both run several times slower on CPU.
- NLTK is the older standard Python NLP library, built more for teaching and research than a production extraction pipeline.
- A cloud NLP API (AWS Comprehend, Google Cloud Natural Language) was considered and rejected: it means sending candidate personal data to a third party and paying per request at scale.
- spaCy's own larger transformer pipeline (`en_core_web_trf`) was also not used, for the same reason as the mpnet comparison above: meaningfully slower for a modest accuracy gain.

**GradientBoostingClassifier (scikit-learn)** ships as part of scikit-learn, which this project already depends on, so it adds no extra install to the deployed container. Alternatives considered:
- XGBoost is generally the stronger performer for this kind of small tabular classification task, and `ml/matching/trainer.py` already switches to it automatically the moment it is installed. It was not added to `requirements/` because pulling in a large compiled dependency was not worth it until there was enough real training data to make the upgrade matter.
- LightGBM and CatBoost are comparable, well-regarded alternatives in the same family that have not been specifically evaluated for this project.

**SHAP and LIME together** make different tradeoffs, and showing both means no single method is trusted blindly.
- SHAP is the more rigorous of the two, grounded in Shapley values from game theory, and gives the same answer every time it is asked.
- LIME is faster and gives a quick local approximation, but it can give a slightly different answer if asked twice for the same prediction, since it works by sampling nearby examples rather than an exact calculation.
- Anchors was considered: it explains a prediction as a rule rather than a set of weighted factors, which answers a different question than "why this score," so it reads as a separate feature rather than a replacement for either method above.

---

## Model Reliability

Not every model in this stack can honestly claim the same kind of reliability number, and this section says exactly which is which rather than implying they're all equally validated.

**SBERT** does not have an accuracy number computed on this platform's data, and none is claimed here. It is a pretrained model (`all-MiniLM-L6-v2`), and its accuracy has already been measured by the people who built it. On the STS Benchmark, a standard test of how well a model judges two sentences as similar in meaning, it is commonly reported to score in the mid-80s out of 100. On the broader MTEB benchmark, a suite of 56 different language tasks, it averages in the mid-50s out of 100, which is expected since that suite covers far more than similarity matching alone. The exact decimal varies slightly by source (the mid-80s figure ranged from about 82 to 85 across the evaluations checked), which is normal as benchmark code and dataset versions get updated over time, so treat the model's own [Hugging Face card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) and the [public MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) as the source of truth for the current number rather than a fixed figure repeated here. This score measures general sentence similarity, not hiring success, so it is the model's reputation on its own task, not this platform's accuracy.

**spaCy skill extraction** was evaluated directly, since this is the one component that can be checked honestly without any hiring-outcome ground truth. 16 real candidates were sampled at random from the imported datasets (the OpenIntro audit study was excluded, since its "resumes" are short fabricated bio stubs by design, not full free-text CVs). Each was read in full and manually annotated with the skills a recruiter would reasonably tag, then compared against what the extraction pipeline actually produced:

```
n candidates: 16 | true positives: 59 | false positives: 4 | false negatives: 8
precision: 0.9365 | recall: 0.8806 | F1: 0.9077
```

Two of the four false positives are worth naming directly rather than hiding in a summary statistic: the extractor tagged "typescript" on an Oracle/SQL database administrator's resume that never mentions JavaScript or TypeScript, and "statistics" on a SQL Server administrator's resume that never uses that word either. This is a small, fixed, honestly-scoped sample, not a claim about extraction accuracy across the full real candidate pool, and it is reproducible: `python manage.py shell -c "from ml.nlp.skill_extraction_eval import run; run()"` (annotations live in `ml/nlp/skill_extraction_eval.py`).

**GradientBoostingClassifier** cannot honestly be given an accuracy number today. Here is what was actually checked, not assumed. The model saved on this platform right now was trained on 251 examples:

```
251 labeled MatchResult rows: 26 hired=True, 225 hired=False
Of those 251, 0 come from a real candidate and real job pair. All 251 are synthetic.
```

All 251 of those examples are synthetic. None are real people. So an accuracy number from this model today would only show how well it agrees with this platform's own made up hiring simulation, not how well it predicts real hiring, which is why no such number is presented anywhere in this project.

There is one dataset with real hiring outcomes: the OpenIntro audit study, with 4,870 real decisions. That data is sitting in the database. It never made it into this model's training, and the reason is a known, specific one. `apps/applications/signals.py` copies a real hiring outcome onto a match score, but it only runs the moment an application is saved, and only if a match score for that pair already exists at that exact moment. For most of these real applications, matching had not run yet when they were imported, so that copy step found nothing to update and never tried again later.

This was fixable, so it was fixed, in two parts.

First, the backlog: `apps/matching/management/commands/backfill_openintro_match_results.py` scores every one of the 4,812 real application pairs that never had a match score, using only what was already in the database (real resumes, real jobs, and the real skills and embeddings already extracted from them during import, nothing newly downloaded), then labels all 4,870 real applications the way the study itself measured success: a real callback as the positive outcome, no callback as the negative outcome. That gave 392 positive and 4,478 negative real, correctly labeled examples, verified directly against the database after running it.

Second, the actual bug, not just the backlog it left behind: `run_batch_matching_for_job` in `apps/matching/services.py` now checks, every time it runs for a job, whether a real hiring decision already exists for that job, and relabels the results to match. `bulk_create` never fires Django's save signals, which is why the old one-shot sync never caught this in the first place. So the same gap should not happen again for any future real decision, on any job, not just this one dataset.

One thing worth being clear about: the saved model has not been retrained on this new real data yet. 4,870 real labeled examples now exist and are ready to train on, which is a real change from before, but the model actually running on this platform has not learned from them. Retraining it is a separate next step, not something being claimed as already done.

**The counterfactual name-bias probe**, unlike the classifier above, has a real, already-run result. Across 300 real candidate and job pairs and 24 real name variants per resume (drawn from the audit study's own most common White-female, White-male, Black-female, and Black-male coded names), average score movement between White-coded and Black-coded names was 0.0019, statistically indistinguishable from zero. There was some sensitivity to a name being present at all (about 0.056 on average across variants), but it did not consistently favor either group. Reproducible from `ml/fairness/name_bias_probe.py`.

**Fairness math** (Disparate Impact Ratio, Demographic Parity Difference) is not a predictive model and doesn't need a reliability claim in the same sense; it is arithmetic over whatever real decisions an organization has actually logged, and is exactly as reliable as that data entry.

---

## Real-World Data

Real job postings and candidate profiles come from eight public datasets, deduplicated by content hash both within and across sources so the same posting or resume is never counted twice, even when two datasets happen to scrape the same original source.

| Source | What it provides | Imported |
|---|---|---|
| [EMSCAD](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) | Real job postings | 15,546 |
| [jobs.am](https://www.kaggle.com/datasets/madhab/jobposts) (Armenian CareerCenter, 2004 to 2015) | Real job postings | 17,718 |
| [LinkedIn Job Postings](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) (2023 to 2024) | Real job postings | 1,949 |
| [Djinni Recruitment Dataset](https://huggingface.co/collections/lang-uk/djinni-recruitment-dataset) | Real job postings and anonymized real candidate CVs | 2,000 + 2,000 |
| [Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) (livecareer.com samples) | Real template resumes | 2,481 |
| [resume_corpus](https://github.com/florex/resume_corpus) | Real resumes | 2,000 |
| [Resume-Classification-Dataset](https://github.com/noran-mohamed/Resume-Classification-Dataset) | Real resumes | 1,821 |
| [Resume-Callback Audit Study](https://www.openintro.org/data/index.php?data=resume) (Bertrand & Mullainathan, 2004) | Real job postings, audit-study resumes, and real employer callback decisions | 1,323 jobs, 4,870 applications, 392 real callbacks |

For every real candidate, protected attributes (gender, ethnicity, age range, disability status) are left blank; they're never fabricated for a real person. The one exception is the audit study above, where race and gender coded names were the actual controlled variable in the original research, so those records carry that name-coded label explicitly rather than presenting it as self-reported data. Only the fully synthetic dataset, generated rather than based on any real person, models protected attributes directly, specifically so the fairness audit has a realistic scenario to test itself against.

Full sourcing detail, license citations, what was deliberately excluded and why, and a notice-and-takedown contact are on the in-app [About page](https://sheikhkmmtahmid-hiringai-platform.hf.space/about) rather than duplicated here, since that page is generated from the same dataset metadata the importers use and won't drift out of sync with what's actually loaded.

> LinkedIn and Indeed are never scraped directly by this platform. The LinkedIn dataset above is a third-party Kaggle republish, used with the sourcing caveats documented on the About page.

---

## Running the Platform (Quick Start)

The platform needs a MySQL-compatible database (TiDB Cloud's free serverless tier is what this project actually runs against; a local MySQL 8+ works too for development) and Redis. Once those are reachable, you need **4 terminals open simultaneously**.

### Terminal 1: Redis (run once; skip if already running)
```powershell
docker run -d -p 6379:6379 --name redis redis:7-alpine
```
> If it says "name already in use", Redis is already running, so skip this step.

### Terminal 2: Celery Worker (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform"
.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo
```

### Terminal 3: Django Backend (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform"
.venv\Scripts\Activate.ps1
python manage.py runserver 8001
```

### Terminal 4: React Frontend (keep open)
```powershell
cd "d:\Explainable AI Hiring Intelligence Platform\frontend"
npm install
npm run dev
```
> `npm install` is only needed the first time.

Once all 4 are running:

| Interface | URL |
|---|---|
| **HR Frontend (React)** | `http://localhost:3000` |
| **Backend API** | `http://127.0.0.1:8001/api/v1/` |
| **Django Admin** | `http://127.0.0.1:8001/admin/` |

Login with the superuser account you created during setup.

---

## How to Run

### Local Development

**Prerequisites:** Python 3.11, Node 20, a MySQL 8+ or TiDB-compatible database, Redis 7

**Step 1: Clone and enter the project**
```bash
cd "Explainable AI Hiring Intelligence Platform"
```

**Step 2: Activate the virtual environment**
```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**Step 3: Copy environment variables**
```bash
cp .env.example .env
# Edit .env: set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, and DB_PORT for your TiDB
# or MySQL instance, plus REDIS_URL and any API keys you have
```

**Step 4: Install Python dependencies**
```bash
pip install -r requirements/development.txt
```

**Step 5: Run migrations**
```bash
python manage.py migrate
```

**Step 6: Create a superuser**
```bash
python manage.py createsuperuser
```

**Step 7: Download the spaCy model**
```bash
python -m spacy download en_core_web_sm
```

**Step 8: Start the development server**
```bash
python manage.py runserver 8001
```

**Step 9: Start Celery worker (in a separate terminal)**
```bash
celery -A config worker --loglevel=info --pool=solo
```

**Step 10: Start the React frontend (in a separate terminal)**
```bash
cd frontend
npm install
npm run dev
```

The API is available at `http://localhost:8001/api/v1/`, the admin panel at `http://localhost:8001/admin/`, and the frontend dev server proxies `/api` to it automatically.

---

### Container Deployment

The `Dockerfile` builds a single image containing both the Django backend and the compiled React frontend, served by Gunicorn. This is exactly what runs on the live Hugging Face Space.

```bash
docker build -t hiringai-platform .
docker run -p 7860:7860 --env-file .env hiringai-platform
```

`start.sh` runs migrations, collects static files, starts a Celery worker in the background, and then starts Gunicorn on port 7860. Point `DB_*` and `REDIS_URL` in `.env` at reachable services before running it. There's no bundled database or Redis container in this image, since the deployed Space connects out to TiDB Cloud and a managed Redis instance rather than running them alongside it.

---

### Importing Real Datasets

Each real dataset has its own management command under `apps/ingestion/management/commands/`, for example:

```bash
python manage.py import_emscad
python manage.py import_jobsam
python manage.py import_linkedin_jobs --limit 2000
python manage.py import_djinni_jobs --limit 2000
python manage.py import_djinni_candidates --limit 2000
python manage.py import_resume_cc0
python manage.py import_resume_florex --limit 2000
python manage.py import_resume_noranmohamed --limit 2000
python manage.py import_openintro_audit_study
```

Every command accepts `--limit N` (`0` for unlimited) and is safe to re-run: already-imported rows are skipped by source and content hash, not re-inserted.

---

### Generating Synthetic Data

```bash
# Generate 500 synthetic candidates
curl -X POST http://localhost:8001/api/v1/synthetic/generate/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"kind": "candidates", "count": 500}'

# Generate 200 synthetic jobs
curl -X POST http://localhost:8001/api/v1/synthetic/generate/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"kind": "jobs", "count": 200}'
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
| `DJANGO_SECRET_KEY` | Django secret key | required, no default |
| `DJANGO_DEBUG` | Enable debug mode | `False` |
| `DJANGO_SETTINGS_MODULE` | Settings module path | `config.settings.development` |
| `DB_NAME` | Database name | `hiringai` |
| `DB_USER` | Database username | `root` |
| `DB_PASSWORD` | Database password | empty |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `4000` (TiDB default) |
| `REDIS_URL` | Redis cache URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/2` |
| `BACKEND_BASE_URL` | Where the backend itself is reachable (for payment provider callbacks) | `http://localhost:8001` |
| `ADZUNA_APP_ID` / `ADZUNA_API_KEY` | Adzuna live job ingestion API | empty |
| `JOOBLE_API_KEY` / `THE_MUSE_API_KEY` | Additional live job ingestion APIs | empty |
| `SBERT_MODEL_NAME` | Sentence-BERT model | `all-MiniLM-L6-v2` |
| `SPACY_MODEL_NAME` | spaCy model | `en_core_web_sm` |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe billing | empty, provider shows as not configured if blank |
| `SSLCOMMERZ_STORE_ID` / `SSLCOMMERZ_STORE_PASSWORD` / `SSLCOMMERZ_SANDBOX` | SSLCommerz billing | empty |
| `SENTRY_DSN` | Error tracking (production) | empty |

---

## Design Principles

- **Explainability first:** Every match score has a human-readable explanation. No black-box outputs.
- **Fairness by design, audited against reality:** Fairness reports run against real recruiter decisions once they exist, and say so plainly when they can't yet.
- **Honest about real vs. synthetic:** Every job and candidate record is tagged with its source; protected attributes are never fabricated for a real person.
- **Global applicability:** No hard-coded country or region assumptions. All location fields are free-form strings.
- **Service layer architecture:** Business logic lives in `services.py` files, not in views or models.
- **Async ML tasks:** All embedding generation and batch matching runs as Celery tasks, keeping the API non-blocking.
- **Multi-tenant by default:** Every model that holds an organization's data is scoped to that organization, not bolted on after the fact.
- **Modular apps:** Each Django app has a single responsibility and can be extended independently.

---

## Academic Context

This project demonstrates:

- NLP-based semantic matching using transformer embeddings (SBERT)
- Explainable AI using SHAP and LIME for hiring decision transparency
- Algorithmic fairness analysis with Disparate Impact, Demographic Parity, and real external benchmark (EEOC) comparison
- Integration and honest disclosure of real-world, licensed public datasets alongside a purpose-built synthetic data generator
- Multi-tenant, production-shaped Django architecture with async processing and pluggable billing

It serves as both a portfolio project and a research prototype for the academic paper:

> *"An Explainable and Fair NLP-Based Candidate to Job Matching Framework Using Django and Multi-Source Recruitment Data"*

---

## License

This project is for academic and portfolio purposes.
