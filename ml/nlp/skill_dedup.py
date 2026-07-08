"""
Duplicate / near-duplicate detection for proposed skill names, checked
before anything new is added to SkillTaxonomy -- whether discovered by the
ESCO sync, mined from the platform's own job/CV corpus, or typed in by a
user adding a new skill while posting a job.

Three passes, cheapest and most certain first:
  1. Exact match against canonical names + aliases (case-insensitive)
  2. Fuzzy string match (catches typos / minor formatting variants,
     e.g. "Scikit Learn" vs "Scikit-Learn")
  3. SBERT embedding similarity (catches semantic near-duplicates that
     string matching can't -- "ML" vs "Machine Learning")
"""
import difflib
import logging
import threading

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.87
EMBEDDING_THRESHOLD = 0.80

_embedding_cache = None  # {skill_id: np.ndarray}
_lock = threading.Lock()


def _build_embedding_cache():
    from apps.taxonomy.models import SkillTaxonomy
    from ml.embeddings.encoder import encode_batch

    skills = list(SkillTaxonomy.objects.all())
    if not skills:
        return {}
    vectors = encode_batch([s.canonical_name for s in skills])
    return {skill.id: vec for skill, vec in zip(skills, vectors)}


def _get_embedding_cache():
    global _embedding_cache
    with _lock:
        if _embedding_cache is None:
            _embedding_cache = _build_embedding_cache()
    return _embedding_cache


def reload_embedding_cache():
    """Force a rebuild on next call -- call after SkillTaxonomy changes
    (new skill approved, alias added, etc.)."""
    global _embedding_cache
    with _lock:
        _embedding_cache = None


def find_similar_skill(proposed_name: str):
    """
    Check a proposed skill name against the existing taxonomy.

    Returns (matched_skill_or_None, similarity_score_or_None, match_type)
    where match_type is "exact", "fuzzy", "embedding", or None if nothing
    close enough was found.
    """
    from apps.taxonomy.models import SkillTaxonomy

    name_lower = proposed_name.strip().lower()
    if not name_lower:
        return None, None, None

    skills = list(SkillTaxonomy.objects.all())

    # Pass 1: exact match against canonical name or any alias
    for skill in skills:
        if skill.canonical_name.strip().lower() == name_lower:
            return skill, 1.0, "exact"
        if any((alias or "").strip().lower() == name_lower for alias in (skill.aliases or [])):
            return skill, 1.0, "exact"

    # Pass 2: fuzzy string match
    best_skill, best_score = None, 0.0
    for skill in skills:
        for candidate in [skill.canonical_name, *list(skill.aliases or [])]:
            score = difflib.SequenceMatcher(None, name_lower, candidate.strip().lower()).ratio()
            if score > best_score:
                best_score, best_skill = score, skill
    if best_skill is not None and best_score >= FUZZY_THRESHOLD:
        return best_skill, round(best_score, 4), "fuzzy"

    # Pass 3: SBERT embedding similarity
    try:
        from ml.embeddings.encoder import encode_text, cosine_similarity_score

        cache = _get_embedding_cache()
        if cache:
            proposed_vec = encode_text(proposed_name).tolist()
            skill_by_id = {s.id: s for s in skills}
            best_id, best_emb_score = None, 0.0
            for skill_id, vec in cache.items():
                score = cosine_similarity_score(proposed_vec, vec.tolist())
                if score > best_emb_score:
                    best_emb_score, best_id = score, skill_id
            if best_id is not None and best_emb_score >= EMBEDDING_THRESHOLD:
                return skill_by_id[best_id], round(best_emb_score, 4), "embedding"
    except Exception as exc:
        logger.warning("Embedding-based skill dedup check failed: %s", exc)

    return None, None, None
