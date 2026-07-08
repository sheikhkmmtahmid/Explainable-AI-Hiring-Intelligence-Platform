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


def _sample_weights(y: np.ndarray) -> np.ndarray:
    """Balanced sample weights -- with hiring data typically ~90% negative,
    an unweighted fit mostly learns to predict the majority class."""
    from sklearn.utils.class_weight import compute_sample_weight
    return compute_sample_weight("balanced", y)


def _cross_validate(X: np.ndarray, y: np.ndarray, n_positive: int, n_negative: int) -> dict:
    """
    Stratified k-fold evaluation. A single train/test split is unreliable
    at the sample sizes this model typically has to work with -- with
    e.g. 13 positive examples, a 20% test split leaves only ~3 of them,
    and ROC-AUC swings wildly depending on which 3 happened to land in
    the test fold. Averaging over several folds gives an honest estimate
    of both the score and its uncertainty (std).
    """
    from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score
    from sklearn.model_selection import StratifiedKFold

    n_splits = max(2, min(5, n_positive, n_negative))
    if n_splits < 2:
        return {}

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    roc_aucs, pr_aucs, precisions, recalls, f1s = [], [], [], [], []

    for train_idx, test_idx in skf.split(X, y):
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        fold_clf = _build_classifier()
        weights = _sample_weights(y_train)
        fold_clf.fit(X_train, y_train, sample_weight=weights)

        y_prob = fold_clf.predict_proba(X_test)[:, 1]
        y_pred = fold_clf.predict(X_test)

        try:
            roc_aucs.append(roc_auc_score(y_test, y_prob))
        except Exception:
            pass
        try:
            pr_aucs.append(average_precision_score(y_test, y_prob))
        except Exception:
            pass
        precisions.append(precision_score(y_test, y_pred, zero_division=0))
        recalls.append(recall_score(y_test, y_pred, zero_division=0))
        f1s.append(f1_score(y_test, y_pred, zero_division=0))

    def _mean_std(values):
        if not values:
            return None, None
        arr = np.array(values, dtype=np.float64)
        return float(arr.mean()), float(arr.std())

    roc_mean, roc_std = _mean_std(roc_aucs)
    pr_mean, pr_std = _mean_std(pr_aucs)

    return {
        "cv_folds": n_splits,
        "roc_auc_mean": round(roc_mean, 4) if roc_mean is not None else None,
        "roc_auc_std": round(roc_std, 4) if roc_std is not None else None,
        "pr_auc_mean": round(pr_mean, 4) if pr_mean is not None else None,
        "pr_auc_std": round(pr_std, 4) if pr_std is not None else None,
        "precision_mean": round(float(np.mean(precisions)), 4) if precisions else None,
        "recall_mean": round(float(np.mean(recalls)), 4) if recalls else None,
        "f1_mean": round(float(np.mean(f1s)), 4) if f1s else None,
    }


def train_and_save(min_samples: int = MIN_SAMPLES, output_path: Path = MODEL_PATH) -> dict:
    """
    Build training data, evaluate via stratified k-fold CV, fit the final
    model on all data with balanced sample weights, and save to disk.

    Returns a summary dict with sample counts and CV metrics (ROC-AUC and
    PR-AUC mean/std, precision/recall/F1). PR-AUC and precision/recall are
    reported alongside ROC-AUC because with heavily imbalanced hiring data
    (typically ~90% "not hired"), ROC-AUC alone can look deceptively
    reasonable while the model is barely better than predicting the
    majority class -- PR-AUC and recall on the positive class make that
    visible.

    Raises ValueError if there are not enough labelled samples.
    """
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

    cv_metrics = _cross_validate(X, y, n_positive, n_negative)
    if cv_metrics:
        logger.info(
            "CV (%d folds): ROC-AUC %.4f ± %.4f | PR-AUC %.4f ± %.4f | "
            "precision %.4f | recall %.4f | F1 %.4f",
            cv_metrics["cv_folds"],
            cv_metrics["roc_auc_mean"] or 0, cv_metrics["roc_auc_std"] or 0,
            cv_metrics["pr_auc_mean"] or 0, cv_metrics["pr_auc_std"] or 0,
            cv_metrics["precision_mean"] or 0, cv_metrics["recall_mean"] or 0, cv_metrics["f1_mean"] or 0,
        )
    else:
        logger.info("Too few samples per class for cross-validation -- skipping CV metrics.")

    # Final model: fit on all available data (with balanced weights) so the
    # deployed model benefits from every labelled example, not just a split.
    clf = _build_classifier()
    clf.fit(X, y, sample_weight=_sample_weights(y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, output_path)
    logger.info("Model saved to %s", output_path)

    return {
        "n_samples": n_samples,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "cv_folds": cv_metrics.get("cv_folds"),
        "roc_auc_mean": cv_metrics.get("roc_auc_mean"),
        "roc_auc_std": cv_metrics.get("roc_auc_std"),
        "pr_auc_mean": cv_metrics.get("pr_auc_mean"),
        "pr_auc_std": cv_metrics.get("pr_auc_std"),
        "precision_mean": cv_metrics.get("precision_mean"),
        "recall_mean": cv_metrics.get("recall_mean"),
        "f1_mean": cv_metrics.get("f1_mean"),
        "model_path": str(output_path),
    }
