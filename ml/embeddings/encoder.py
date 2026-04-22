"""
SBERT-based text encoder with lazy loading and caching.
Thread-safe model singleton to avoid re-loading on each task.
"""
import logging
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_model_name: Optional[str] = None


def _get_model():
    global _model, _model_name
    with _model_lock:
        if _model is None:
            from django.conf import settings
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, "SBERT_MODEL_NAME", "all-MiniLM-L6-v2")
            logger.info("Loading SBERT model: %s", model_name)
            _model = SentenceTransformer(model_name)
            _model_name = model_name
    return _model


def get_model_name() -> str:
    global _model_name
    if _model_name is None:
        from django.conf import settings
        _model_name = getattr(settings, "SBERT_MODEL_NAME", "all-MiniLM-L6-v2")
    return _model_name


def encode_text(text: str) -> np.ndarray:
    """Encode a single text string to a dense vector."""
    model = _get_model()
    # Truncate very long texts to avoid OOM
    text = text[:5000]
    return model.encode(text, normalize_embeddings=True)


def encode_batch(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Encode a list of texts efficiently."""
    model = _get_model()
    texts = [t[:5000] for t in texts]
    return model.encode(texts, batch_size=batch_size, normalize_embeddings=True)


def cosine_similarity_score(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two pre-normalised vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
