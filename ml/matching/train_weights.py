"""
Train a logistic regression model on (feature_vector → hired/shortlisted) labels
to learn optimal hybrid score weights from synthetic recruiter decisions.

What this replaces
------------------
The current hybrid scorer uses fixed heuristic weights:
    semantic=0.50, skill_overlap=0.30, experience=0.15, education=0.05

After running this script those weights are replaced by the logistic regression
coefficients, which are learned from actual (simulated) recruiter decisions.

The trained weights are saved to:
    ml/matching/learned_weights.json

The scorer in apps/matching/services.py reads this file at startup if it exists,
falling back to the heuristic defaults otherwise.

Usage
-----
    python ml/matching/train_weights.py
    python ml/matching/train_weights.py --output ml/matching/learned_weights.json
    python ml/matching/train_weights.py --scenario gender_bias_tech  # only use one scenario
    python ml/matching/train_weights.py --min-samples 500            # require more data
    python ml/matching/train_weights.py --evaluate                   # show CV scores after training
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path(__file__).parent / "learned_weights.json"

FEATURE_NAMES = [
    "semantic_score",
    "skill_overlap_score",
    "experience_score",
    "education_score",
]

# Fallback weights used when the file does not exist
HEURISTIC_WEIGHTS = {
    "semantic_score": 0.50,
    "skill_overlap_score": 0.30,
    "experience_score": 0.15,
    "education_score": 0.05,
}

RELEVANT_STATUSES = {"shortlisted", "interview", "offer", "hired"}


# ──────────────────────────────────────────────────────────────────────────────
# Feature extraction
# ──────────────────────────────────────────────────────────────────────────────

def _education_score(candidate_edu: str, required_edu: str = "bachelor") -> float:
    edu_order = ["high_school", "associate", "bachelor", "master", "phd"]
    try:
        c = edu_order.index(candidate_edu) if candidate_edu in edu_order else 0
        r = edu_order.index(required_edu) if required_edu in edu_order else 2
        return 1.0 if c >= r else c / max(r, 1)
    except ValueError:
        return 0.5


def build_feature_matrix(applications) -> tuple[np.ndarray, np.ndarray, list]:
    """
    Extract feature vectors and labels from Application + MatchResult records.

    Returns:
        X      — (n_samples, n_features) feature matrix
        y      — (n_samples,) binary label (1 = relevant, 0 = rejected)
        ids    — list of (candidate_id, job_id) for traceability
    """
    from apps.matching.models import MatchResult

    X_rows = []
    y_labels = []
    ids = []

    # Pre-fetch match results for fast lookup
    app_keys = {(a.candidate_id, a.job_id): a for a in applications}
    match_results = {
        (mr.candidate_id, mr.job_id): mr
        for mr in MatchResult.objects.filter(
            candidate_id__in=[a.candidate_id for a in applications],
            job_id__in=[a.job_id for a in applications],
        )
    }

    missing_match = 0
    for app in applications:
        key = (app.candidate_id, app.job_id)
        mr = match_results.get(key)
        if mr is None:
            missing_match += 1
            continue

        candidate = app.candidate
        edu = _education_score(candidate.highest_education or "")

        features = [
            float(mr.semantic_score or 0.0),
            float(mr.skill_overlap_score or 0.0),
            float(mr.experience_score or 0.0),
            float(edu),
        ]
        label = 1 if app.status in RELEVANT_STATUSES else 0

        X_rows.append(features)
        y_labels.append(label)
        ids.append(key)

    if missing_match:
        logger.warning(
            "%d applications skipped: no MatchResult found. "
            "Run batch matching before training.",
            missing_match,
        )

    return np.array(X_rows, dtype=np.float32), np.array(y_labels, dtype=np.int32), ids


# ──────────────────────────────────────────────────────────────────────────────
# Training
# ──────────────────────────────────────────────────────────────────────────────

def train(
    X: np.ndarray,
    y: np.ndarray,
    evaluate: bool = False,
) -> tuple[dict, dict | None]:
    """
    Fit logistic regression and extract feature weights.

    Returns:
        weights     — dict mapping feature name → normalised weight
        cv_results  — cross-validation scores (if evaluate=True), else None
    """
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    cv_results = None
    if evaluate:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_validate(
            model, X, y, cv=cv,
            scoring=["accuracy", "roc_auc", "f1"],
            return_train_score=True,
        )
        cv_results = {
            "accuracy_mean": round(float(scores["test_accuracy"].mean()), 4),
            "accuracy_std": round(float(scores["test_accuracy"].std()), 4),
            "roc_auc_mean": round(float(scores["test_roc_auc"].mean()), 4),
            "roc_auc_std": round(float(scores["test_roc_auc"].std()), 4),
            "f1_mean": round(float(scores["test_f1"].mean()), 4),
            "f1_std": round(float(scores["test_f1"].std()), 4),
        }
        logger.info("Cross-validation results:")
        for k, v in cv_results.items():
            logger.info("  %-20s %.4f", k, v)

    model.fit(X, y)
    clf = model.named_steps["clf"]
    raw_coefs = clf.coef_[0]

    # Normalise coefficients so they sum to 1.0 (keeping positive only)
    clipped = np.clip(raw_coefs, 0, None)
    total = clipped.sum()
    if total == 0:
        logger.warning("All coefficients are non-positive. Falling back to heuristic weights.")
        weights = HEURISTIC_WEIGHTS.copy()
    else:
        normalised = clipped / total
        weights = {
            name: round(float(w), 6)
            for name, w in zip(FEATURE_NAMES, normalised)
        }

    logger.info("Learned weights:")
    for name, w in weights.items():
        logger.info("  %-25s %.4f  (raw coef: %+.4f)", name, w, raw_coefs[FEATURE_NAMES.index(name)])

    # Full classification report on training set
    y_pred = model.predict(X)
    logger.info("\nTraining set classification report:\n%s", classification_report(y, y_pred))

    return weights, cv_results


# ──────────────────────────────────────────────────────────────────────────────
# Persistence
# ──────────────────────────────────────────────────────────────────────────────

def save_weights(weights: dict, path: Path, metadata: dict | None = None) -> None:
    payload = {
        "weights": weights,
        "feature_names": FEATURE_NAMES,
        "metadata": metadata or {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info("Weights saved to %s", path)


def load_weights(path: Path | None = None) -> dict:
    """Load learned weights if they exist, otherwise return heuristic defaults."""
    target = path or DEFAULT_OUTPUT
    if target.exists():
        with open(target) as f:
            payload = json.load(f)
        return payload["weights"]
    return HEURISTIC_WEIGHTS.copy()


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Train logistic regression to learn hybrid score weights from recruiter labels"
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to save learned_weights.json")
    parser.add_argument("--scenario", help="Only use applications from a specific bias scenario (by name substring)")
    parser.add_argument("--min-samples", type=int, default=100, help="Minimum labelled samples required (default: 100)")
    parser.add_argument("--evaluate", action="store_true", help="Run 5-fold cross-validation")
    args = parser.parse_args()

    from apps.applications.models import Application

    qs = Application.objects.filter(
        is_synthetic=True,
    ).select_related("candidate", "job")

    if args.scenario:
        qs = qs.filter(recruiter_notes__icontains=args.scenario)

    applications = list(qs)
    logger.info("Loaded %d synthetic applications", len(applications))

    if len(applications) < args.min_samples:
        logger.error(
            "Not enough labelled data: %d samples (minimum: %d). "
            "Generate synthetic applications first:\n"
            "  POST /api/v1/synthetic/generate/ {\"kind\": \"applications\", \"scenario\": \"no_bias\"}",
            len(applications), args.min_samples,
        )
        sys.exit(1)

    logger.info("Building feature matrix...")
    X, y, ids = build_feature_matrix(applications)
    logger.info("Feature matrix: %s  |  Positives: %d  |  Negatives: %d", X.shape, y.sum(), (y == 0).sum())

    if X.shape[0] < args.min_samples:
        logger.error(
            "Only %d samples with match results found. "
            "Run batch matching first:\n"
            "  POST /api/v1/matching/trigger/{job_id}/",
            X.shape[0],
        )
        sys.exit(1)

    logger.info("Training logistic regression...")
    weights, cv_results = train(X, y, evaluate=args.evaluate)

    metadata = {
        "n_samples": int(X.shape[0]),
        "n_positive": int(y.sum()),
        "n_negative": int((y == 0).sum()),
        "scenario_filter": args.scenario,
        "cv_results": cv_results,
        "heuristic_baseline": HEURISTIC_WEIGHTS,
    }

    save_weights(weights, Path(args.output), metadata)

    logger.info("\n=== Weight comparison ===")
    logger.info("%-25s %-12s %-12s", "Feature", "Heuristic", "Learned")
    for name in FEATURE_NAMES:
        logger.info(
            "  %-23s %-12.4f %-12.4f",
            name,
            HEURISTIC_WEIGHTS[name],
            weights[name],
        )


if __name__ == "__main__":
    main()
