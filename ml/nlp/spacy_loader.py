"""
Lazy-loaded spaCy model singleton, mirroring ml.embeddings.encoder's
pattern for the SBERT model -- avoids reloading the model on every parse.
"""
import logging
import threading

logger = logging.getLogger(__name__)

_nlp = None
_nlp_lock = threading.Lock()


def get_nlp():
    """Return the shared spaCy pipeline, loading it on first use."""
    global _nlp
    with _nlp_lock:
        if _nlp is None:
            import spacy
            from django.conf import settings
            model_name = getattr(settings, "SPACY_MODEL_NAME", "en_core_web_sm")
            logger.info("Loading spaCy model: %s", model_name)
            _nlp = spacy.load(model_name)
    return _nlp
