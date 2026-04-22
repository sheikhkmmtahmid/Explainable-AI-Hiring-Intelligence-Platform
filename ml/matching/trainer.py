"""
Trains a classification model (GradientBoosting or XGBoost if installed) on
MatchResult rows that have a hiring outcome recorded (hired=True/False).

The trained model is saved to ml/models/scorer.joblib and is used by
trained_scorer.py to replace the fixed-weight hybrid scorer.

This module is called by the train_scorer management command:
    python manage.py train_scorer

It can also be imported directly for scripting or tests.
"""
import logging
from pathlib import Path

import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "scorer.joblib"
FEATURE_NAMES = [
    "semantic_similarity",
    "required_skill_overlap",
    "preferred_skill_overlap",
    "experience_ratio",
    "education_match",
    "seniority_match",
    "location_compatibility",
]
MIN_SAMPLES = 50


def _build_classifier():
    """Return XGBoost classifier if available, otherwise GradientBoosting."""
    try:
        from xgboost import XGBClassifier
        logger.info("Using XGBoost classifier")
        return XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        logger.info("XGBoost not installed -- using GradientBoostingClassifier")
        return GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )


def build_training_data() -> tuple[np.ndarray, np.ndarray]:
    """
    Pull all MatchResult rows with a recorded hiring outcome and build
    (feature_matrix, label_vector).

    Requires Django to be set up -- call from management command or
    after django.setup().
    """
    from apps.matching.models import MatchResult
    from .scorer import build_feature_vector

    labelled = list(
        MatchResult.objects.filter(hired__isnull=False)
        .select_related("candidate", "job")
        .prefetch_related(
            "candidate__skills",
            "job__skill_requirements",
        )
    )

    if not labelled:
        return np.empty((0, len(FEATURE_NAMES)), dtype=np.float32), np.empty(0, dtype=np.int32)

    X_rows = []
    y_labels = []

    for mr in labelled:
        candidate = mr.candidate
        job = mr.job

        candidate_skills = list(candidate.skills.values_list("skill_name", flat=True))
        job_required = list(job.skill_requirements.filter(is_required=True).values_list("skill_name", flat=True))
        job_preferred = list(job.skill_requirements.filter(is_required=False).values_list("skill_name", flat=True))

        min_exp = 0.0
        for req in job.skill_requirements.filter(min_years__isnull=False):
            if req.min_years and req.min_years > min_exp:
                min_exp = float(req.min_years)

        candidate_data = {
            "semantic_score": float(mr.semantic_score or 0.0),
            "skills": candidate_skills,
            "years_of_experience": float(candidate.years_of_experience or 0),
            "highest_education": candidate.highest_education or "",
            "seniority_level": getattr(candidate, "seniority_level", "mid") or "mid",
            "remote_preference": getattr(candidate, "remote_preference", "flexible") or "flexible",
        }
        job_data = {
            "required_skills": job_required,
            "preferred_skills": job_preferred,
            "min_experience_years": min_exp,
            "required_education": "bachelor",
            "experience_level": job.experience_level or "mid",
            "work_model": job.work_model or "onsite",
        }

        try:
            fv = build_feature_vector(candidate_data, job_data)
            X_rows.append(fv)
            y_labels.append(1 if mr.hired else 0)
        except Exception as exc:
            logger.warning("Skipping MatchResult id=%s: %s", mr.id, exc)

    if not X_rows:
        return np.empty((0, len(FEATURE_NAMES)), dtype=np.float32), np.empty(0, dtype=np.int32)

    return np.array(X_rows, dtype=np.float32), np.array(y_labels, dtype=np.int32)


def train_and_save(min_samples: int = MIN_SAMPLES, output_path: Path = MODEL_PATH) -> dict:
    """
    Build training data, fit the model, save to disk.

    Returns a summary dict with n_samples, n_positive, n_negative, and
    training accuracy.

    Raises ValueError if there are not enough labelled samples.
    """
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    logger.info("Building training data from MatchResult.hired labels...")
    X, y = build_training_data()

    n_samples = len(y)
    n_positive = int(y.sum())
    n_negative = n_samples - n_positive

    logger.info("Samples: %d total | %d hired | %d not hired", n_samples, n_positive, n_negative)

    if n_samples < min_samples:
        raise ValueError(
            f"Not enough labelled data: {n_samples} samples found, "
            f"{min_samples} required. "
            "Set the 'hired' field on MatchResult rows before training."
        )

    if n_positive == 0 or n_negative == 0:
        raise ValueError(
            "Both classes (hired=True and hired=False) must have at least one sample."
        )

    clf = _build_classifier()

    # Only split if we have enough data for a meaningful eval set
    if n_samples >= 100:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]
        accuracy = float(accuracy_score(y_test, y_pred))
        try:
            roc_auc = float(roc_auc_score(y_test, y_prob))
        except Exception:
            roc_auc = None
        logger.info("Test accuracy: %.4f  |  ROC-AUC: %s", accuracy, f"{roc_auc:.4f}" if roc_auc else "n/a")
        # Retrain on full data after evaluation
        clf.fit(X, y)
    else:
        clf.fit(X, y)
        y_pred = clf.predict(X)
        accuracy = float(accuracy_score(y, y_pred))
        roc_auc = None
        logger.info("Training accuracy (no eval split -- too few samples): %.4f", accuracy)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, output_path)
    logger.info("Model saved to %s", output_path)

    return {
        "n_samples": n_samples,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "accuracy": round(accuracy, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc else None,
        "model_path": str(output_path),
    }
