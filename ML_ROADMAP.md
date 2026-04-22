# ML Scorer Roadmap

This document explains why the platform currently uses fixed scoring weights,
what is already built for a trained ML model, and the exact steps to activate it
when real hiring data is available.

---

## Current State

The platform scores candidate-job matches using a weighted formula in
`apps/matching/services.py`:

```
overall_score = 0.50 * semantic + 0.30 * skill_overlap
              + 0.15 * experience + 0.05 * education
```

These weights come from domain knowledge, not from data. They are reasonable
defaults but are not learned from actual hiring decisions.

### Why not a trained model right now

A classification model needs labelled examples: "this candidate was hired" or
"this candidate was rejected." That data does not exist yet because the platform
is new. Training on made-up labels would produce a model that learns noise, not
signal.

The fixed-weight approach is also fully transparent. Anyone can read the weights
and understand exactly how a score was calculated. A black-box classifier would
require SHAP on top of SHAP, which defeats the point of the platform.

---

## What is Already Built

All the code needed to train and activate a real model is in place. Nothing
needs to be written from scratch.

| File | Purpose |
|---|---|
| `apps/matching/models.py` | `MatchResult.hired` field (nullable bool) stores the hiring outcome label |
| `ml/matching/trainer.py` | Builds training data from labelled MatchResult rows, trains the model, saves it |
| `ml/matching/trained_scorer.py` | Loads the saved model, exposes `predict_score()` |
| `apps/matching/management/commands/train_scorer.py` | Management command to run training |
| `apps/matching/services.py` | `_compute_overall()` tries the trained model first, falls back to fixed weights if no model exists |

The fallback is automatic. If `ml/models/scorer.joblib` does not exist, the
system behaves exactly as before. Nothing breaks.

---

## How to Activate the Trained Model

### Step 1: Collect hiring outcome labels

For each hiring decision made, set the `hired` field on the relevant
`MatchResult` row.

From the Django shell:

```python
from apps.matching.models import MatchResult

# Mark a candidate as hired
mr = MatchResult.objects.get(candidate_id=123, job_id=456)
mr.hired = True
mr.save(update_fields=["hired"])

# Mark as not hired
mr.hired = False
mr.save(update_fields=["hired"])
```

You need at least 50 labelled rows to train. More is better. A few hundred
gives a meaningful model. A few thousand gives a reliable one.

Both classes must be present (some hired=True and some hired=False).

### Step 2: Run the training command

```bash
python manage.py train_scorer
```

With options:

```bash
# Require at least 200 labelled samples
python manage.py train_scorer --min-samples 200

# Save model to a custom path
python manage.py train_scorer --output /path/to/model.joblib
```

The command prints accuracy and saves the model to `ml/models/scorer.joblib`.

### Step 3: Restart the server and workers

The model is loaded once at process startup. Restart Django and Celery:

```bash
# Django dev server
Ctrl+C, then: python manage.py runserver

# Celery worker
Ctrl+C, then: celery -A config worker -l info
```

After restart, all new match score calculations will use the trained model.
Existing MatchResult rows are not recalculated automatically -- re-run batch
matching for any jobs you want updated scores for.

---

## What the Model Learns

The model is trained on the same 7-feature vector used by the explainability
layer (`ml/matching/scorer.py`):

| Feature | Description |
|---|---|
| `semantic_similarity` | Cosine similarity between candidate and job SBERT embeddings |
| `required_skill_overlap` | Fraction of required skills the candidate has |
| `preferred_skill_overlap` | Fraction of preferred skills the candidate has |
| `experience_ratio` | Candidate years / job minimum years (capped at 1.5) |
| `education_match` | 1 if candidate education meets the requirement, else 0 |
| `seniority_match` | How close candidate seniority is to the job level (0 to 1) |
| `location_compatibility` | Remote preference vs work model compatibility (0 to 1) |

The model outputs a probability (0 to 1) that a candidate would be hired.
This probability becomes the overall match score.

---

## Upgrading to XGBoost

The trainer automatically uses XGBoost if it is installed. XGBoost usually
gives better results than the default GradientBoosting classifier.

```bash
pip install xgboost
python manage.py train_scorer
```

No other code changes are needed.

---

## Checking Model Status

From the Django shell:

```python
from ml.matching.trained_scorer import is_available
print(is_available())  # True if model is loaded, False if using fixed weights
```

To force a reload after training (without restarting the server):

```python
from ml.matching import trained_scorer
trained_scorer.reload()
```

---

## Rollback

To go back to fixed weights, delete or rename the model file:

```bash
rm ml/models/scorer.joblib
```

Restart the server. The fallback weights take over immediately.
