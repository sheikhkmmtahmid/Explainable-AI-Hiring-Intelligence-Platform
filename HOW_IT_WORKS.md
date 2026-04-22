# How the Explainable AI Hiring Intelligence Platform Works

This document explains what every part of the platform does, how the pieces connect,
and how data moves from a CV upload all the way to a ranked match result with an explanation.
File names are included so you can open the exact file being described.

---

## Table of Contents

1. [Big Picture Overview](#1-big-picture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Folder Structure](#3-project-folder-structure)
4. [Django Apps (Back End)](#4-django-apps-back-end)
5. [ML Layer](#5-ml-layer)
6. [The Full Data Pipeline Step by Step (9 steps)](#6-the-full-data-pipeline-step-by-step)
7. [How Django and Celery Work Together](#7-how-django-and-celery-work-together)
8. [Front End Pages and API Layer](#8-front-end-pages-and-api-layer)
9. [How the Front End Talks to the Back End](#9-how-the-front-end-talks-to-the-back-end)
10. [User Roles and Access Control](#10-user-roles-and-access-control)
11. [Key Configuration Files](#11-key-configuration-files)
12. [Skill and Experience Matching Rules](#12-skill-and-experience-matching-rules)

---

## 1. Big Picture Overview

The platform is a hiring assistant that helps recruiters rank job candidates fairly and transparently.
It does four main things:

1. Reads CVs and pulls out skills, years of experience, and education level.
2. Matches candidates to job posts using an AI similarity model plus skill and experience checks.
3. Explains every match score so a recruiter can see exactly why a candidate ranked where they did.
4. Checks for bias by comparing how often different demographic groups get shortlisted, and flags
   if the gap is too wide.

The back end is built with Django. The ML models run as background jobs via Celery.
The front end is a React app. PostgreSQL stores everything. Redis acts as the message
queue between Django and Celery.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Back end framework | Django + Django REST Framework | HTTP requests, database, business logic |
| Authentication | djangorestframework-simplejwt | Issues and validates JWT tokens |
| Async task queue | Celery | Runs CV parsing, embedding generation, and batch matching in the background |
| Message broker | Redis | Passes task messages between Django and Celery workers |
| Database | PostgreSQL 15 | Stores all data |
| Semantic AI model | SBERT all-MiniLM-L6-v2 | Converts text to 384-dimension vectors for similarity comparison |
| Explainability | Combined SHAP and LIME (custom) | Breaks down why a score is high or low |
| PDF parsing | pdfminer.six | Extracts plain text from PDF files |
| DOCX parsing | python-docx | Extracts plain text from Word documents |
| Front end | React.js + Vite | User interface |
| HTTP client | Axios | Makes API calls from the browser to Django |
| Charts | Recharts | Bar and radar charts on the match and fairness pages |

---

## 3. Project Folder Structure

```
Explainable AI Hiring Intelligence Platform/
|
|-- apps/                        Django apps (12 separate modules)
|   |-- accounts/                User accounts and login
|   |-- candidates/              Candidate profiles, CVs, skills
|   |-- jobs/                    Job postings and skill requirements
|   |-- parsing/                 CV text extraction and skill parsing
|   |-- matching/                Scoring, ranking, and batch matching
|   |-- explainability/          Combined SHAP and LIME explanations
|   |-- fairness/                Bias detection and disparate impact reports
|   |-- applications/            Hiring pipeline and interview scheduling
|   |-- ingestion/               Pulls jobs from external APIs (Adzuna etc.)
|   |-- synthetic_data/          Generates fake data for testing and demos
|   |-- analytics/               Dashboard summary stats
|   |-- taxonomy/                Skill reference list
|
|-- ml/                          Pure ML code (no Django imports)
|   |-- embeddings/
|   |   |-- encoder.py           Loads the SBERT model, encodes text to vectors
|   |-- matching/
|   |   |-- scorer.py            Builds a 7-feature vector for SHAP and LIME
|   |-- explainability/
|   |   |-- shap_explainer.py    SHAP-style weighted feature contributions
|   |   |-- lime_explainer.py    LIME-style perturbation-based contributions
|   |-- fairness/
|   |   |-- metrics.py           Disparate impact and parity calculations
|
|-- config/                      Django project settings and URL routing
|   |-- settings/
|   |   |-- base.py              All Django settings
|   |-- urls.py                  Top-level URL router
|   |-- celery.py                Celery app setup
|
|-- frontend/                    React front end
|   |-- src/
|       |-- api/                 Axios API functions (one file per Django app)
|       |-- pages/               Full-page React components
|       |-- components/          Reusable UI components
|       |-- context/             Auth state management
|
|-- scripts/
|   |-- generate_test_cvs.py     Generates 4 PDF CVs for test candidates
|
|-- data/test_cvs/               PDF CVs for the four test candidates
|-- HOW_IT_WORKS.md              This file
```

---

## 4. Django Apps (Back End)

Each app lives in the `apps/` folder and follows the same pattern:

- `models.py` defines database tables
- `serializers.py` converts records to and from JSON for the API
- `views.py` handles incoming HTTP requests
- `services.py` holds business logic that is not tied to HTTP
- `tasks.py` holds Celery background tasks
- `urls.py` maps URL paths to views

---

### accounts

**Files:** `apps/accounts/models.py`, `apps/accounts/views.py`, `apps/accounts/serializers.py`

Manages user accounts and login.

The `User` model in `models.py` extends Django's built-in user. It adds a `role` field with
four values: `admin`, `recruiter`, `analyst`, and `candidate`.
The role controls what data a user can see.
For example, only admins and recruiters can see all candidates.
A user with the `candidate` role can only see their own profile.

Login works with JWT tokens. A POST to `/api/v1/auth/login/` with a username and password
returns an access token (valid 1 hour) and a refresh token (valid 7 days).
The access token must be included in every subsequent request as a header:
`Authorization: Bearer <token>`.
When the access token expires, the front end uses the refresh token to get a new one
automatically. This logic lives in `frontend/src/api/client.js`.

---

### candidates

**Files:** `apps/candidates/models.py`, `apps/candidates/views.py`, `apps/candidates/services.py`

Stores candidate profiles, uploaded CVs, skills, and work experience.

Key database tables created by `models.py`:

- `Candidate`: one row per person. Stores name, email, location, current title,
  years of experience, education level, expected salary, and protected demographic
  attributes (gender, age range, ethnicity, disability status). The demographic fields
  are only used for fairness analysis and are never given to the AI model.
- `CandidateCV`: one row per uploaded file. A candidate can have many CVs.
  The most recently uploaded one is treated as primary.
- `CandidateSkill`: one row per skill. Stores skill name (always lowercase), category,
  proficiency, and how it was found (parsed from CV, entered manually, or inferred).
- `CandidateExperience`: one row per job in the candidate's history.
- `CandidateEmbedding`: stores the SBERT vector as a JSON list of 384 numbers.

Key service functions in `services.py`:

- `attach_cv(candidate, file, filename)`: saves the uploaded file to disk and creates
  a `CandidateCV` record.
- `add_skill(candidate, skill_name, ...)`: creates or updates a `CandidateSkill` record.
  Always stores the skill name as lowercase so matching is case-insensitive.
- `compute_total_experience(candidate)`: adds up all experience date ranges
  to get total years.

The `CandidateViewSet` in `views.py` supports filtering by `is_synthetic` so the front end
can show separate tabs for real candidates and synthetic test candidates.

---

### jobs

**Files:** `apps/jobs/models.py`, `apps/jobs/views.py`, `apps/jobs/services.py`

Stores job postings and the skills required for each job.

Key database tables:

- `JobPost`: one row per job. Stores title, company, description, requirements text,
  responsibilities text, location, work model (onsite/remote/hybrid), employment type,
  experience level, salary range, and status (draft, active, closed, filled).
  Jobs can come from manual entry or from external APIs like Adzuna.
- `JobSkillRequirement`: one row per skill linked to a job. Has an `is_required` flag
  and a `min_years` field. Skill names are always stored as lowercase.
- `JobEmbedding`: stores the SBERT vector for the job text.

**Automatic skill extraction:**
Every time a job is created or updated (via `perform_create` and `perform_update`
in `views.py`), the function `_extract_skills_from_text(job)` runs automatically.
This function (defined at the bottom of `views.py`) concatenates the job title,
description, requirements, and responsibilities into one string, then passes it
to `extract_skills_from_text()` in `apps/parsing/services.py`.
Any skills found are saved as `JobSkillRequirement` records.
This means you do not need to manually enter skill requirements. Writing the job
description and requirements text is enough.

**Important:** If the requirements and responsibilities fields are left empty,
the system still extracts skills from the description and title.
But a well-written requirements section (one skill or qualification per line)
will produce better results.

There is also a manual `extract_skills` action on the job endpoint
(`POST /jobs/{id}/extract_skills/`) that lets you re-run extraction at any time
without editing the job.

---

### parsing

**Files:** `apps/parsing/services.py`, `apps/parsing/tasks.py`

Reads an uploaded CV file and pulls out structured information.

`services.py` contains:

- `extract_text_from_file(file_path)`: reads a PDF with pdfminer, a DOCX with
  python-docx, or a plain text file directly.
- `extract_skills_from_text(text)`: searches the text (lowercased) for a list of
  skill keywords defined in the `SKILL_PATTERNS` list at the top of the file.
  The list includes terms like `python`, `nlp`, `docker`, `scikit-learn`, etc.
  Matching is case-insensitive because both the text and the patterns are lowercased.
  Matched skills are always stored as lowercase.
- `extract_years_of_experience(text)`: uses a regex to find phrases like
  "5 years of experience" or "3+ years experience".
- `parse_cv_text(text)`: calls the above functions and returns a dictionary with
  keys `skills`, `email`, `phone`, and `years_of_experience`.

`tasks.py` contains the `parse_cv_task` Celery task.
When a CV is uploaded, this task runs in the background and does the following in order:

1. Calls `extract_text_from_file()` to get plain text from the file.
2. Saves the plain text to `CandidateCV.raw_text`.
3. Calls `parse_cv_text()` to get skills, email, phone, and years of experience.
4. Calls `add_skill()` in `apps/candidates/services.py` for each skill found.
5. Recalculates and saves total years of experience on the `Candidate` record.
6. Queues `generate_candidate_embedding_task` in `apps/matching/tasks.py`.

---

### matching

**Files:** `apps/matching/models.py`, `apps/matching/services.py`, `apps/matching/tasks.py`

Compares every candidate to a job post and produces a ranked score for each pair.

Key database tables in `models.py`:

- `MatchResult`: one row per candidate-job pair. Stores five scores (overall,
  semantic, skill overlap, experience, education) and a rank number.
- `MatchBatchRun`: tracks the status of a batch matching job (pending, running,
  done, failed).

The five scores computed in `services.py`:

| Score | How it is computed | Weight |
|---|---|---|
| Semantic | Cosine similarity between candidate SBERT vector and job SBERT vector | 50% |
| Skill overlap | Count of matched required skills divided by total required skills | 30% |
| Experience | Candidate years divided by job required years, capped at 100% | 15% |
| Education | 1.0 if candidate education level meets or exceeds job requirement, else partial | 5% |
| Overall | Weighted sum of all four above | Final ranking |

The `compute_skill_overlap_score(candidate_skills, job_skills)` function in `services.py`
lowercases both skill sets before computing the intersection, so `NLP` and `nlp` always
match each other.

`tasks.py` contains three Celery tasks:

- `generate_candidate_embedding_task(candidate_id)`: builds a text string from the
  candidate's title, summary, skills, and experience titles, then encodes it using
  the SBERT model in `ml/embeddings/encoder.py`. Saves the result as a
  `CandidateEmbedding` record.
- `generate_job_embedding_task(job_id)`: same process for a job. Encodes the job title,
  description, and requirements. Saves as a `JobEmbedding` record.
- `batch_match_job_task(job_id)`: calls `run_batch_matching_for_job(job_id)` in
  `services.py`, which loops through every candidate with an embedding and computes
  all five scores. Results are bulk-inserted into the database and then ranked.

---

### explainability

**Files:** `apps/explainability/models.py`, `apps/explainability/services.py`,
`apps/explainability/views.py`, `apps/explainability/serializers.py`

Explains why a candidate received the score they did.

**The explanation is always a single combined result.** The system runs both SHAP and LIME
internally, combines them (SHAP weighted 60%, LIME weighted 40%), and shows one unified
explanation. There are no separate SHAP and LIME buttons for the user.

The `ExplanationReport` model in `models.py` stores one report per candidate-job pair:

- `feature_importances`: a dictionary of plain-English feature names mapped to their
  combined importance score (for example `{"profile alignment": 1.0, "required skills": 0.8}`).
- `top_positive_factors`: list of factors that helped the score (for example
  "Required skills matched", "Years of experience").
- `top_negative_factors`: list of factors that hurt the score (for example
  "Missing required skills"). Only shown if the importance value is above a significance
  threshold (0.08). Near-zero noise values are filtered out.
- `matching_skills`: skills the candidate has that the job requires.
- `missing_skills`: required skills the candidate does not have.
- `summary_text`: a plain English sentence like "Overall match: 73.4%.
  Matches 7 required skills. Missing: terraform, kubernetes."

The `generate_explanation(match_result_id)` function in `services.py` does the following:

1. Fetches the `MatchResult` and its linked `Candidate` and `JobPost`.
2. Lowercases both candidate skills and job required skills before comparing,
   so skill matching is always case-insensitive.
3. Builds a 7-number feature vector using `build_feature_vector()` from
   `ml/matching/scorer.py`.
4. Runs `explain_match()` from `ml/explainability/shap_explainer.py` to get
   SHAP-style contributions.
5. Runs `explain_with_lime()` from `ml/explainability/lime_explainer.py` to get
   LIME-style correlations.
6. Normalises both sets of values to the same scale, then combines them:
   `combined = (shap_normalised * 0.6) + (lime_normalised * 0.4)`.
7. Maps the internal ML feature names to plain English display names.
8. Applies a significance threshold of 0.08. Anything below this is not shown
   in the top factors panels. This prevents near-zero noise from appearing as
   meaningful results.
9. Saves the result as an `ExplanationReport` record.

The `ExplanationView` in `views.py` handles two requests:

- `GET /explainability/{match_result_id}/`: returns the existing report.
- `POST /explainability/{match_result_id}/`: generates (or regenerates) the report
  and returns it. Both GET and POST return the exact same JSON shape.

The `ExplanationReportSerializer` in `serializers.py` adds five extra fields read
from the linked `MatchResult`: `overall_score`, `semantic_score`, `skill_overlap_score`,
`experience_score`, and `education_score`. These are needed by the front end to draw
the score bars and radar chart.

---

### fairness

**Files:** `apps/fairness/models.py`, `apps/fairness/services.py`,
`apps/fairness/views.py`, `apps/fairness/serializers.py`

Checks whether the matching scores are fair across demographic groups.

Key database tables in `models.py`:

- `FairnessReport`: one row per job per protected attribute. Stores the disparate
  impact ratio, overall selection rate, and a bias flag.
- `SubgroupMetric`: one row per group per report. Stores the group value (e.g. "female"),
  total candidates, shortlisted count, and selection rate.

The `compute_fairness_report(job_id, protected_attribute)` function in `services.py`:

1. Fetches all `MatchResult` rows for the job.
2. Groups candidates by the value of the protected attribute (for example by `gender`).
3. For each group: counts total candidates and those with `overall_score >= 0.5`
   (the shortlist threshold). Divides to get the selection rate.
4. Computes the Disparate Impact Ratio: lowest group rate divided by highest group rate.
5. Sets the bias flag to `True` if the ratio is below 0.8 (the legal 4/5 rule).
6. Saves a `FairnessReport` and one `SubgroupMetric` per group.

The `FairnessReportView` in `views.py` checks whether any `MatchResult` rows exist
for the job before computing. If none exist, it returns a clear error:
"No matching results found for this job. Run matching first."
This prevents showing a misleading 0.000 result for jobs that have never been matched.

The four supported protected attributes are: `gender`, `age_range`, `ethnicity`,
`disability_status`. These fields are stored on the `Candidate` model and are never
given to the SBERT model or used in scoring. The matching system is blind to demographics.
The fairness check only reads them after scores have already been computed.

---

### applications

**Files:** `apps/applications/models.py`, `apps/applications/views.py`

Tracks where a candidate is in the hiring process for a specific job.

Status flow: applied, screening, shortlisted, interview, offer, and then either
hired, rejected, or withdrawn.

Key database tables:

- `Application`: links one candidate to one job with a current status, match scores
  copied from `MatchResult`, and reviewer notes.
- `ApplicationNote`: a timestamped comment added by a recruiter.
- `InterviewSlot`: a scheduled interview with a date, duration, type
  (phone/video/technical/final), meeting link, and outcome.

---

### ingestion

**Files:** `apps/ingestion/services.py`, `apps/ingestion/tasks.py`

Pulls real job listings from external APIs and saves them as `JobPost` records.

`ingest_from_adzuna()` in `services.py` calls the Adzuna API.
`normalise_adzuna_job()` maps the Adzuna field names to the platform's `JobPost` fields.
`save_jobs_from_raw()` inserts jobs while skipping any that already exist,
matched by source name plus external ID.

---

### synthetic_data

**Files:** `apps/synthetic_data/generators.py`, `apps/synthetic_data/tasks.py`,
`apps/synthetic_data/management/commands/create_test_candidates.py`

Generates fake but realistic candidates, jobs, and applications for testing and demos.

The `BiasScenario` dataclass in `generators.py` lets you define different shortlist
rates per demographic group to simulate biased hiring outcomes. This is used to make
the Fairness dashboard show meaningful results even without real data.

The management command `create_test_candidates` in
`management/commands/create_test_candidates.py` creates four specific test candidates
at varying match levels for the Credit Risk Data Scientist job. It also generates
their SBERT embeddings and runs batch matching. The four candidates are:

- Aisha Okonkwo: senior credit risk data scientist, strong match
- James Chen: e-commerce data scientist, partial match
- Priya Sharma: deep learning ML engineer, weak match
- Tom Williams: junior developer, very weak match

Their PDF CVs are stored in `data/test_cvs/` and are generated by `scripts/generate_test_cvs.py`.

---

### analytics

**Files:** `apps/analytics/services.py`, `apps/analytics/views.py`

Provides summary numbers for the dashboard.

`get_platform_summary()` returns totals: candidates, synthetic candidates, jobs,
active jobs, applications, and match results.

`build_pipeline_snapshot()` counts how many applications are in each hiring stage
for a given job.

---

## 5. ML Layer

The `ml/` folder contains all machine learning code. It has no Django imports and
can be tested or run on its own.

---

### ml/embeddings/encoder.py

Loads the SBERT model and provides three functions:

- `encode_text(text)`: converts a single string into a 384-number vector.
  The text is truncated to 5000 characters first. The output is normalised (length = 1),
  which makes cosine similarity fast to compute.
- `encode_batch(texts)`: does the same for a list of strings at once.
- `cosine_similarity_score(vec_a, vec_b)`: computes the dot product of two normalised
  vectors. The result is between 0.0 (completely different) and 1.0 (identical).

The model is loaded once and kept in memory (lazy singleton pattern). Loading takes
a few seconds, so it only happens on the first call.

---

### ml/matching/scorer.py

Builds the 7-number feature vector used by the SHAP and LIME explainers.
The function `build_feature_vector(candidate_data, job_data)` computes:

1. Semantic score (from SBERT cosine similarity)
2. Required skill overlap ratio (candidate skills divided by required skills)
3. Preferred skill overlap ratio (same but for preferred skills)
4. Experience ratio (candidate years divided by job required years, capped at 1.5)
5. Education match (1.0 if candidate education is equal or higher, else 0.0)
6. Seniority match (1.0 minus the normalised distance between seniority levels)
7. Location compatibility (from a matrix: remote-to-remote scores 1.0,
   remote-to-onsite scores 0.2, etc.)

Both candidate skills and job skills are lowercased before comparison
so `NLP`, `nlp`, and `Nlp` all count as the same skill.

---

### ml/explainability/shap_explainer.py

The `explain_match(feature_vector)` function multiplies each of the 7 feature values
by a fixed weight array `[0.50, 0.20, 0.10, 0.10, 0.05, 0.03, 0.02]`.
Each product is the feature's contribution (called a SHAP value here).
The results are sorted by absolute contribution, largest first.

This is called pseudo-SHAP because it uses fixed weights rather than computing
true Shapley values from a trained model.

---

### ml/explainability/lime_explainer.py

The `explain_with_lime(feature_vector)` function generates 100 random variations of
the feature vector by adding small Gaussian noise to each number.
It clips all values to stay between 0 and 1.
It computes a score for each variation using the same weights as matching.
It then measures the correlation between each feature's changes and the score changes.
A high correlation means that feature had a strong local influence.

This is called pseudo-LIME because it approximates the LIME method without
fitting a full local linear model.

Any NaN correlation values (which happen when a feature has zero variance, for example
when skill overlap is always 0) are replaced with 0.0 before combining.

---

### ml/fairness/metrics.py

Contains standalone functions for computing fairness metrics:

- `disparate_impact(group_rates)`: returns the lowest group rate divided by the highest.
  A value below 0.8 means the lowest group is selected less than 80% as often as the top
  group, which fails the legal 4/5 rule.
- `demographic_parity_difference(group_rates)`: returns the highest rate minus the lowest.
- `equal_opportunity_difference(group_tpr)`: the same calculation but on true positive rates.
- `flag_bias(di_ratio, threshold=0.8)`: returns True if the ratio is below the threshold.
- `summarise_fairness(subgroup_data)`: calls all the above and returns one summary dictionary.

---

## 6. The Full Data Pipeline Step by Step

This section walks through exactly what happens from the moment a recruiter posts a job
and uploads a candidate CV to the moment a ranked explanation appears on screen.

---

### Step 1: Recruiter creates a job post

The recruiter fills in the job form on the front end (`frontend/src/pages/JobCreate.jsx`).
The form includes a title, description, and requirements text.
The hint text under Requirements and Responsibilities says to enter one item per line,
because the system splits on newlines when displaying them as a bullet list.

The front end calls `createJob(payload)` in `frontend/src/api/jobs.js`,
which posts to `POST /api/v1/jobs/`.

Django receives this in `JobPostViewSet.perform_create()` in `apps/jobs/views.py`.
It does three things:

1. Saves the `JobPost` record to the database using `JobPostCreateSerializer`.
2. Calls `_extract_skills_from_text(job)` (defined at the bottom of `views.py`).
   This function concatenates the title, description, requirements, and responsibilities,
   passes the combined text to `extract_skills_from_text()` in `apps/parsing/services.py`,
   and saves any found skills as `JobSkillRequirement` records.
   Skills from all text fields are captured, so even if Requirements is left empty,
   skills mentioned in the Description are still saved.
3. Queues `generate_job_embedding_task(job.id)` on Celery.

The Celery task encodes the job text to a 384-number SBERT vector using
`encode_text()` in `ml/embeddings/encoder.py` and saves it as a `JobEmbedding` record.

The same `_extract_skills_from_text()` function also runs on every job update,
so editing the requirements text always re-syncs the skill requirements.

---

### Step 2: Recruiter uploads a candidate CV

The recruiter opens a candidate profile (`frontend/src/pages/CandidateDetail.jsx`)
and uploads a PDF.

The front end calls `uploadCV(candidateId, formData)` in `frontend/src/api/candidates.js`,
which posts to `POST /api/v1/candidates/{id}/upload_cv/`.

Django receives this in `CandidateViewSet.upload_cv()` in `apps/candidates/views.py`.
It calls `attach_cv(candidate, file, file.name)` in `apps/candidates/services.py`,
which saves the file to disk and creates a `CandidateCV` record.
It then queues `parse_cv_task(cv.id)` on Celery.

---

### Step 3: CV parsing (background task)

The Celery worker picks up `parse_cv_task` from `apps/parsing/tasks.py`.

1. Calls `extract_text_from_file(file_path)` in `apps/parsing/services.py`.
   Uses pdfminer for PDFs, python-docx for DOCX files, or reads directly for TXT files.
   Saves the plain text to `CandidateCV.raw_text`.
2. Calls `parse_cv_text(raw_text)` which calls `extract_skills_from_text(text)`.
   This function lowercases the entire CV text and searches for each keyword in the
   `SKILL_PATTERNS` list in `apps/parsing/services.py`.
   Found skills are always stored as lowercase in the `CandidateSkill` table.
3. Calls `add_skill(candidate, skill_name, ...)` in `apps/candidates/services.py`
   for each found skill. `add_skill` always calls `.strip().lower()` on the name
   before saving, so there is no way a skill gets stored with mixed case.
4. Recalculates and saves total years of experience on the `Candidate` record.
5. Queues `generate_candidate_embedding_task(candidate.id)`.

---

### Step 4: Candidate embedding generation (background task)

The Celery worker picks up `generate_candidate_embedding_task`
from `apps/matching/tasks.py`.

The helper function `_build_candidate_text(candidate)` in the same file
concatenates:
- The candidate's current job title
- Their profile summary
- All their skill names
- All their experience job titles

This combined text is passed to `encode_text()` in `ml/embeddings/encoder.py`.
The SBERT model returns a 384-number normalised vector.
Django saves it as a `CandidateEmbedding` record.
The candidate is now ready to be matched.

---

### Step 5: Batch matching (background task)

The recruiter clicks "Run Matching" on the job detail page
(`frontend/src/pages/JobDetail.jsx`).

The front end calls `triggerMatching(jobId)` in `frontend/src/api/matching.js`,
which posts to `POST /api/v1/matching/trigger/{job_id}/`.

Django creates a `MatchBatchRun` record (status = pending) and queues
`batch_match_job_task(job_id)` from `apps/matching/tasks.py`.

The Celery worker runs `run_batch_matching_for_job(job_id)` in `apps/matching/services.py`:

1. Loads the job's 384-number vector from `JobEmbedding`.
2. Loads all candidates that have a `CandidateEmbedding` record.
3. For each candidate, computes five scores:
   - Semantic: `cosine_similarity_score(candidate_vector, job_vector)` from
     `ml/embeddings/encoder.py`.
   - Skill overlap: `compute_skill_overlap_score(candidate_skills, job_required_skills)`
     in `apps/matching/services.py`. Both skill sets are lowercased before comparison.
   - Experience: candidate years divided by required years, capped at 1.5, then to 1.0.
   - Education: ordinal comparison of education levels.
   - Overall: `(0.50 * semantic) + (0.30 * skill) + (0.15 * experience) + (0.05 * education)`.
4. Bulk-inserts all `MatchResult` rows into the database at once.
5. Sorts by overall score and writes rank numbers (rank 1 = best match).
6. Sets `MatchBatchRun.status = done`.

---

### Step 6: Front end shows ranked results

The recruiter's browser is on the match results page
(`frontend/src/pages/MatchResults.jsx`) or sees the top 10 on the job detail page
(`frontend/src/pages/JobDetail.jsx`).

The front end calls `getTopCandidates(jobId, 20)` in `frontend/src/api/matching.js`,
which fetches from `GET /api/v1/matching/top-candidates/{job_id}/`.

Django returns the top candidates ordered by rank. The front end renders each one
with four score bars: Semantic, Skills, Experience, and Education.

---

### Step 7: Comparing two candidates side by side

On the match results page the recruiter can tick checkboxes next to any two candidates.
A "Compare" button appears once exactly two are selected and navigates to
`frontend/src/pages/CandidateCompare.jsx`.

The compare page calls `getMatchResult(matchIdA)` and `getMatchResult(matchIdB)` in
`frontend/src/api/matching.js` (which fetches from `GET /api/v1/matching/results/{id}/`)
and `getCandidate()` for each, then `getJob(jobId)` -- three parallel requests.

From the returned data it computes matching and missing skills for each candidate
by comparing their skill lists against `job.skill_requirements`.

The page renders:
- Two profile cards side by side with name, title, experience, education, location,
  and overall score. A "Higher Match" badge appears on the card with the better score.
- A radar chart with two overlapping lines (red for candidate A, blue for candidate B).
- A metric table with five rows (Overall, Semantic, Skills, Experience, Education).
  Each row shows both values with a "Better" badge on the higher side.
- Separate matching skills and missing skills tag clouds for each candidate.
- A link to each candidate's full explanation page.

No new back-end code was needed for this feature. It reuses the existing match result
and candidate endpoints that were already in place.

---

### Step 8: Explanation generation

The recruiter clicks "Explain" next to a candidate.
The front end navigates to `frontend/src/pages/ExplanationDetail.jsx`.

On load, the page calls `getExplanation(matchId)` in `frontend/src/api/explainability.js`.
If no explanation exists yet, it automatically calls `generateExplanation(matchId, 'shap')`
and shows the result. There is no manual step needed.

Django routes both requests to `ExplanationView` in `apps/explainability/views.py`.
A POST request calls `generate_explanation(match_result_id)` in
`apps/explainability/services.py`, which does the following:

1. Fetches the `MatchResult` and its linked `Candidate` and `JobPost`.
2. Lowercases both candidate skills and job required skills before comparing.
   This means `NLP` and `nlp` are treated as the same skill.
3. Computes matched skills (intersection) and missing skills (required minus candidate).
4. Calls `build_feature_vector(candidate_data, job_data)` from `ml/matching/scorer.py`
   to produce a 7-number array.
5. Calls `explain_match(feature_vector)` from `ml/explainability/shap_explainer.py`
   to get SHAP-style contributions.
6. Calls `explain_with_lime(feature_vector)` from `ml/explainability/lime_explainer.py`
   to get LIME-style correlations.
7. Replaces any NaN LIME values with 0.0 (NaN happens when a feature is always 0,
   such as when the candidate has no skills in common).
8. Normalises both sets to the same scale, then combines:
   `combined = (shap_normalised * 0.6) + (lime_normalised * 0.4)`.
9. Maps internal ML names to plain English display names
   (for example `semantic_similarity` becomes `profile alignment`).
10. Applies a significance threshold of 0.08. Features below this threshold are
    not shown in the "Strengths" or "Areas to Note" panels. This prevents
    near-zero noise from appearing as meaningful results.
11. Saves an `ExplanationReport` record and returns it via
    `ExplanationReportSerializer`, which also attaches the five match scores
    from the linked `MatchResult` record.

The front end renders:
- A large overall score percentage.
- A radar chart with four axes (Semantic, Skills, Experience, Education).
- A score breakdown with four bars.
- A "What Drove This Score" bar chart using the combined importances.
- A "Matching Skills" tag cloud (green) and "Missing Skills" tag cloud (amber).
- A "Strengths" list and "Areas to Note" list.
- A plain-English summary sentence.
- A "Refresh" button to regenerate the explanation.

---

### Step 9: Fairness check

The recruiter opens `frontend/src/pages/FairnessDashboard.jsx`,
selects a job and a protected attribute (for example `gender`),
and clicks "Run Analysis".

The front end calls `generateFairnessReport(jobId, 'gender')`
in `frontend/src/api/fairness.js`, which posts to `POST /api/v1/fairness/{job_id}/`.

`FairnessReportView.post()` in `apps/fairness/views.py` first checks whether
any `MatchResult` rows exist for the job. If none exist, it returns an error:
"No matching results found for this job. Run matching first."

If match results exist, it calls `compute_fairness_report(job_id, 'gender')`
in `apps/fairness/services.py`:

1. Fetches all `MatchResult` rows for the job.
2. Groups candidates by gender value.
3. For each group: counts total, counts those with overall score above 0.5,
   and divides to get the selection rate.
4. Computes Disparate Impact Ratio = lowest group rate divided by highest group rate.
5. Sets `bias_flag = True` if the ratio is below 0.8.
6. Saves a `FairnessReport` and one `SubgroupMetric` per group.

The front end draws a bar chart with one bar per demographic group.
A horizontal reference line at 80% marks the legal threshold.
The summary cards show the Disparate Impact Ratio, Demographic Parity Difference,
and a Bias Flag (DETECTED in red, NONE in green).

---

## 7. How Django and Celery Work Together

Django handles HTTP (receiving requests, validating input, returning responses)
but does not run slow tasks inside a request. Instead, it hands them to Celery via Redis.

Here is how the handoff works:

1. A Django view receives a request (for example, CV upload).
2. The view saves the minimum data to the database (the file record, a job ID).
3. The view calls `some_task.delay(record_id)`. This puts a message into Redis:
   "run this task with this ID".
4. The view immediately returns a response to the browser.
   The browser does not wait for ML processing.
5. A separate Celery worker process is always running. It reads messages from Redis
   and runs the tasks one by one.
6. The task finishes and writes its results to the database.
7. The front end can poll a status endpoint or simply refresh to see the results.

The three main background workflows are:

- CV parsing (`parse_cv_task` in `apps/parsing/tasks.py`): triggered when a CV
  is uploaded.
- Embedding generation (`generate_candidate_embedding_task` and
  `generate_job_embedding_task` in `apps/matching/tasks.py`): triggered at the end
  of CV parsing and when a job is created or updated.
- Batch matching (`batch_match_job_task` in `apps/matching/tasks.py`): triggered
  when the recruiter clicks Run Matching.

---

## 8. Front End Pages and API Layer

The front end is a single-page React application. It never talks to the database
directly. It only calls the Django REST API over HTTP.

---

### Pages

| File | Route | What it shows |
|---|---|---|
| `frontend/src/pages/Dashboard.jsx` | `/` | Overview with stat cards and recent activity |
| `frontend/src/pages/JobList.jsx` | `/jobs` | Tabbed list: My Jobs, Active, All Jobs |
| `frontend/src/pages/JobCreate.jsx` | `/jobs/new` | Form to post a new job |
| `frontend/src/pages/JobDetail.jsx` | `/jobs/{id}` | Job info, Requirements bullet list, Responsibilities bullet list, top matched candidates, edit, delete |
| `frontend/src/pages/CandidateList.jsx` | `/candidates` | Tabbed list with pagination: My Candidates, Synthetic, All |
| `frontend/src/pages/CandidateCreate.jsx` | `/candidates/new` | Form to add a candidate manually with CV drag-and-drop upload |
| `frontend/src/pages/CandidateDetail.jsx` | `/candidates/{id}` | Full profile, CV history, skills, inline edit, delete |
| `frontend/src/pages/MatchResults.jsx` | `/matching/{job_id}` | All candidates ranked by score with four score bars; tick two checkboxes to compare them side by side |
| `frontend/src/pages/CandidateCompare.jsx` | `/matching/{job_id}/compare/{match_id_a}/{match_id_b}` | Side-by-side comparison of two candidates: scores, radar chart, skills matched and missing |
| `frontend/src/pages/ExplanationDetail.jsx` | `/matching/{job_id}/explain/{match_id}` | Combined SHAP and LIME explanation, radar chart, score breakdown, strengths, areas to note, missing skills |
| `frontend/src/pages/FairnessDashboard.jsx` | `/fairness` | Bar chart of selection rates by demographic group, disparate impact ratio, bias flag |

---

### API Layer

Each file in `frontend/src/api/` holds functions that call one category of Django endpoints.

- `frontend/src/api/client.js`: the Axios instance. Reads the JWT token from localStorage
  and adds it to every request. If a request returns 401, the interceptor calls the refresh
  endpoint, saves the new token, and retries the original request.
- `frontend/src/api/auth.js`: `login(username, password)`, `getMe()`
- `frontend/src/api/candidates.js`: `getCandidates(params)`, `getCandidate(id)`,
  `createCandidate(data)`, `updateCandidate(id, data)`, `deleteCandidate(id)`,
  `uploadCV(id, formData)`, `deleteCV(candidateId, cvId)`
- `frontend/src/api/jobs.js`: `getJobs(params)`, `getJob(id)`, `createJob(data)`,
  `updateJob(id, data)`, `deleteJob(id)`
- `frontend/src/api/matching.js`: `triggerMatching(jobId)`, `getMatchResults(jobId)`,
  `getMatchResult(matchId)`, `getTopCandidates(jobId, n)`
- `frontend/src/api/explainability.js`: `getExplanation(matchResultId)`,
  `generateExplanation(matchResultId, method)`
- `frontend/src/api/fairness.js`: `getFairnessReport(jobId)`,
  `generateFairnessReport(jobId, attribute)`

---

### Reusable Components

| File | What it does |
|---|---|
| `frontend/src/components/Layout.jsx` | Wraps every authenticated page with sidebar and header |
| `frontend/src/components/Sidebar.jsx` | Navigation menu with logo and user info at the bottom |
| `frontend/src/components/LogoIcon.jsx` | Custom SVG logo: person silhouette with AI network nodes and a checkmark badge |
| `frontend/src/components/LoadingSpinner.jsx` | Spinning animation shown while API calls are in flight |
| `frontend/src/components/EmptyState.jsx` | Centered icon, text, and optional action button for empty lists |
| `frontend/src/components/ScoreBar.jsx` | Horizontal progress bar coloured green (high) or red (low) |
| `frontend/src/components/StatCard.jsx` | Dashboard card with icon, large number, and label |
| `frontend/src/components/ConfirmDialog.jsx` | Modal popup with Cancel and Confirm buttons for destructive actions |

---

## 9. How the Front End Talks to the Back End

Every user action on the front end eventually becomes an HTTP request to the Django API.
Here are three concrete examples.

---

**Recruiter logs in:**

1. User types username and password and clicks Sign In in `frontend/src/pages/Login.jsx`.
2. The page calls `login(username, password)` from `frontend/src/api/auth.js`.
3. Axios posts `{ username, password }` to `POST /api/v1/auth/login/`.
4. Django's `LoginView` in `apps/accounts/views.py` validates credentials and returns
   `{ access, refresh, user }`.
5. The front end stores tokens in localStorage.
6. `frontend/src/api/client.js` adds `Authorization: Bearer <token>` to all future requests.

---

**Recruiter runs batch matching:**

1. User opens a job detail page and clicks "Run Matching".
2. `frontend/src/pages/JobDetail.jsx` calls `triggerMatching(jobId)` from
   `frontend/src/api/matching.js`.
3. Axios posts to `POST /api/v1/matching/trigger/25978/`.
4. Django creates a `MatchBatchRun` record and queues the Celery task. Returns 202 immediately.
5. The front end polls `GET /api/v1/matching/top-candidates/25978/` every few seconds.
6. When results appear, the page renders the ranked candidate list.

---

**Recruiter opens an explanation:**

1. User clicks "Explain" next to a candidate in the match results.
2. The browser navigates to `frontend/src/pages/ExplanationDetail.jsx`.
3. On load the page calls `getExplanation(matchId)` from
   `frontend/src/api/explainability.js`.
4. If no explanation exists (404 response), the page automatically calls
   `generateExplanation(matchId, 'shap')`.
5. Django runs the combined SHAP and LIME computation in
   `apps/explainability/services.py` and returns the result.
6. The page renders the radar chart, score bars, feature importance bars,
   matching skills, missing skills, and summary text.

---

## 10. User Roles and Access Control

Role checks happen in Django views, not on the front end.
The front end can hide buttons, but the API enforces the actual rules.

| Role | What they can do |
|---|---|
| `admin` | See all candidates and jobs, run matching and fairness reports, manage users |
| `recruiter` | See all candidates and jobs, post jobs, run matching and fairness reports |
| `analyst` | Read-only access to all candidates, jobs, match results, and fairness reports |
| `candidate` | Can only see and edit their own profile |

The key check is in `apps/candidates/views.py`, inside `get_queryset()`:

```python
if user.role in ("admin", "recruiter", "analyst"):
    qs = Candidate.objects.all()
else:
    qs = Candidate.objects.filter(user=user)
```

If the logged-in user has the `candidate` role, they only get back their own record.
Admins, recruiters, and analysts get all records.

An additional `is_synthetic` query parameter can be passed to filter the list:
`is_synthetic=true` returns only auto-generated test candidates,
`is_synthetic=false` returns only real candidates.
This is used by the tabs on `frontend/src/pages/CandidateList.jsx`.

---

## 11. Key Configuration Files

### config/settings/base.py

All Django settings are here:

- Database connection to PostgreSQL (credentials read from environment variables).
- Celery broker URL pointing to Redis.
- JWT token lifetimes: 1 hour for access tokens, 7 days for refresh tokens.
- CORS settings allowing the React front end at `localhost:3000` to call
  the API at `localhost:8000`.
- `SBERT_MODEL_NAME = "all-MiniLM-L6-v2"` sets which sentence transformer model to use.
- `MATCH_SCORE_THRESHOLD = 0.5` is the cutoff used in fairness analysis to determine
  whether a candidate counts as shortlisted.

### config/urls.py

The central URL router mounts all app URL patterns under `/api/v1/`:

```
/api/v1/auth/             accounts app
/api/v1/candidates/       candidates app
/api/v1/jobs/             jobs app
/api/v1/matching/         matching app
/api/v1/explainability/   explainability app
/api/v1/fairness/         fairness app
/api/v1/applications/     applications app
/api/v1/analytics/        analytics app
/api/v1/ingestion/        ingestion app
/api/v1/taxonomy/         taxonomy app
/api/v1/synthetic/        synthetic_data app
/api/v1/parsing/          parsing app
```

### config/celery.py

Creates the Celery application, points it at Django settings, and tells it to
automatically discover `tasks.py` files in all Django apps. This is how Celery knows
about `parse_cv_task`, `batch_match_job_task`, and all the others.

### frontend/src/api/client.js

The Axios instance used by all API functions. Adds the JWT token to every request.
If a 401 error comes back, it calls the refresh endpoint, saves the new token, and
retries the failed request. This means the user stays logged in without interruption
as long as their refresh token is valid (7 days).

---

## 12. Skill and Experience Matching Rules

### Case sensitivity

All skill names are normalised to lowercase at every point in the pipeline:

- `extract_skills_from_text()` in `apps/parsing/services.py` lowercases the entire
  CV text before pattern matching. The `SKILL_PATTERNS` list is already lowercase.
- `add_skill()` in `apps/candidates/services.py` calls `.strip().lower()` before saving.
- `extract_and_attach_skills()` in `apps/jobs/services.py` calls `.strip().lower()` before saving.
- `_extract_skills_from_text()` in `apps/jobs/views.py` also lowercases before saving.
- `compute_skill_overlap_score()` in `apps/matching/services.py` lowercases both sets
  before computing the intersection.
- `build_feature_vector()` in `ml/matching/scorer.py` lowercases both sets.
- `generate_explanation()` in `apps/explainability/services.py` lowercases both sets
  before computing matched and missing skills.

Result: `NLP`, `nlp`, and `Nlp` are all treated as identical everywhere in the platform.

### How skills are extracted from a job

When a job is saved, `_extract_skills_from_text(job)` in `apps/jobs/views.py` runs.
It concatenates the title, description, requirements, and responsibilities into one string
and passes it to `extract_skills_from_text()` in `apps/parsing/services.py`.
Skills are pulled from all text fields, not just Requirements.
So leaving Requirements empty does not stop skills from being extracted if they appear
in the Description or title.

### How experience score is computed

In `apps/matching/services.py`, the function `compute_experience_score(candidate_years, job_years)`:

- Divides candidate years of experience by the job's required years.
- Caps the result at 1.5 (so 10 years for a 5-year job gives 1.5, not 2.0).
- Clamps the final value to a maximum of 1.0 (100%).
- If the job has no experience requirement, the candidate gets 1.0 automatically.

### How education score is computed

Education levels are mapped to numbers in `apps/matching/services.py`:
`high_school = 1`, `associate = 2`, `bachelor = 3`, `master = 4`, `phd = 5`.
If the candidate's level is equal to or higher than the job's requirement, the score is 1.0.
Otherwise it is a partial credit based on the gap.

### Significance threshold in explanations

In `apps/explainability/services.py`, features with a combined importance below 0.08
(in absolute value) are excluded from the "Strengths" and "Areas to Note" panels.
This prevents near-zero noise from LIME perturbations from appearing as meaningful results.
Features still appear in the "What Drove This Score" bar chart regardless of threshold.
