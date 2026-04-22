"""
LIME-based explanation stub.
Provides local interpretable explanations by perturbing feature inputs.
"""
import logging
import numpy as np

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


def explain_with_lime(feature_vector: np.ndarray, n_samples: int = 100) -> dict:
    """
    Approximate LIME by sampling perturbations of the feature vector.
    For production: use lime.lime_tabular.LimeTabularExplainer.
    """
    base_score = float(np.dot(feature_vector, [0.50, 0.20, 0.10, 0.10, 0.05, 0.03, 0.02]))
    rng = np.random.default_rng(seed=42)

    perturbations = rng.normal(loc=0, scale=0.1, size=(n_samples, len(feature_vector)))
    perturbed = np.clip(feature_vector + perturbations, 0.0, 1.0)

    weights = [0.50, 0.20, 0.10, 0.10, 0.05, 0.03, 0.02]
    scores = (perturbed * weights).sum(axis=1)

    correlations = np.corrcoef(perturbed.T, scores)[:-1, -1]

    lime_values = []
    for name, val, corr in zip(FEATURE_NAMES, feature_vector.tolist(), correlations.tolist()):
        lime_values.append({
            "feature": name,
            "value": round(float(val), 4),
            "lime_weight": round(float(corr), 4),
            "direction": "positive" if corr > 0 else "negative",
        })

    lime_values.sort(key=lambda x: abs(x["lime_weight"]), reverse=True)

    return {
        "lime_values": lime_values,
        "base_score": round(base_score, 4),
        "top_features": lime_values[:5],
    }
