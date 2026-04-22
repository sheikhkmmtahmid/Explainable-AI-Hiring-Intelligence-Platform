"""
SHAP-based explainability for match scores.
Uses a LinearExplainer on the feature vector produced by ml.matching.scorer.
"""
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "semantic_similarity",
    "required_skill_overlap",
    "preferred_skill_overlap",
    "experience_ratio",
    "education_match",
    "seniority_match",
    "location_compatibility",
]

FEATURE_WEIGHTS = np.array([0.50, 0.20, 0.10, 0.10, 0.05, 0.03, 0.02], dtype=np.float32)


def explain_match(feature_vector: np.ndarray) -> dict:
    """
    Compute pseudo-SHAP values as weighted feature contributions.
    For true SHAP, integrate shap.LinearExplainer with a trained model.
    """
    contributions = feature_vector * FEATURE_WEIGHTS
    total = contributions.sum()

    shap_values = []
    for name, val, contrib in zip(FEATURE_NAMES, feature_vector.tolist(), contributions.tolist()):
        shap_values.append({
            "feature": name,
            "value": round(float(val), 4),
            "shap_value": round(float(contrib), 4),
            "direction": "positive" if contrib > 0 else "negative",
        })

    shap_values.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "shap_values": shap_values,
        "base_value": 0.0,
        "predicted_score": round(float(total), 4),
        "top_positive": [s for s in shap_values if s["direction"] == "positive"][:3],
        "top_negative": [s for s in shap_values if s["direction"] == "negative"][:3],
    }
