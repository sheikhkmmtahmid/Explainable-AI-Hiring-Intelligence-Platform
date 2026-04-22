"""
Loads a pre-trained classifier from ml/models/scorer.joblib and turns its
probability output into a 0-1 match score.

If the model file does not exist, predict_score() returns None and the caller
falls back to the fixed-weight hybrid scorer in services.py. Nothing breaks.

The model file is created by running:
    python manage.py train_scorer
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "scorer.joblib"

_model = None
_model_loaded = False


def _load_model():
    """Attempt to load the model once. Subsequent calls are no-ops."""
    global _model, _model_loaded
    if _model_loaded:
        return
    _model_loaded = True
    if not MODEL_PATH.exists():
        logger.debug("No trained scorer found at %s -- using fixed-weight fallback", MODEL_PATH)
        return
    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        logger.info("Trained scorer loaded from %s", MODEL_PATH)
    except Exception as exc:
        logger.warning("Could not load trained scorer: %s -- using fixed-weight fallback", exc)
        _model = None


def is_available() -> bool:
    """Return True if a trained model is loaded and ready."""
    _load_model()
    return _model is not None


def predict_score(feature_vector: np.ndarray) -> Optional[float]:
    """
    Return a match score in [0, 1] using the trained model, or None if no
    model is available (caller should fall back to fixed-weight scorer).

    Args:
        feature_vector: 1-D numpy array produced by
                        ml.matching.scorer.build_feature_vector()
    """
    _load_model()
    if _model is None:
        return None
    try:
        fv = np.array(feature_vector, dtype=np.float32).reshape(1, -1)
        prob = _model.predict_proba(fv)[0, 1]
        return float(np.clip(prob, 0.0, 1.0))
    except Exception as exc:
        logger.warning("trained_scorer.predict_score failed: %s -- using fixed-weight fallback", exc)
        return None


def reload():
    """Force reload the model from disk. Useful after running train_scorer."""
    global _model, _model_loaded
    _model = None
    _model_loaded = False
    _load_model()
