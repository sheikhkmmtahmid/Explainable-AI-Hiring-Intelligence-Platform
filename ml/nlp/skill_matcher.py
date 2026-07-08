"""
Skill extraction using spaCy's PhraseMatcher against SkillTaxonomy.

Replaces plain substring search (which false-positives on things like
matching "java" inside "javascript", and can't resolve aliases like "JS"
to "JavaScript") with proper tokenized, word-boundary-aware matching.

The matcher is built once per process from SkillTaxonomy rows (canonical
name + aliases) and cached -- rebuilding it on every CV parse would mean
a DB query plus pattern compilation for each request.
"""
import logging
import threading

logger = logging.getLogger(__name__)

_matcher = None
_category_by_canonical = None
_lock = threading.Lock()


def _build_matcher():
    from spacy.matcher import PhraseMatcher
    from apps.taxonomy.models import SkillTaxonomy
    from .spacy_loader import get_nlp

    nlp = get_nlp()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    category_by_canonical = {}

    rows = list(SkillTaxonomy.objects.all())
    for row in rows:
        terms = [row.canonical_name] + list(row.aliases or [])
        patterns = [nlp.make_doc(term) for term in terms]
        matcher.add(row.canonical_name, patterns)
        category_by_canonical[row.canonical_name] = row.category

    logger.info("Skill PhraseMatcher built from %d taxonomy rows", len(rows))
    return matcher, category_by_canonical


def _get_matcher():
    global _matcher, _category_by_canonical
    with _lock:
        if _matcher is None:
            _matcher, _category_by_canonical = _build_matcher()
    return _matcher, _category_by_canonical


def reload_matcher():
    """Force a rebuild on next call -- use after editing SkillTaxonomy."""
    global _matcher, _category_by_canonical
    with _lock:
        _matcher = None
        _category_by_canonical = None


def extract_skills_with_taxonomy(text: str) -> list[dict]:
    """
    Return skills found in `text`, matched against SkillTaxonomy (canonical
    names + aliases). Each result maps back to the canonical skill name,
    so "JS", "ECMAScript", and "JavaScript" all resolve to one entry.

    Returns the same shape as the legacy extract_skills_from_text():
    a list of {"skill_name": <lowercase canonical>, "category": <str>}.
    """
    if not text or not text.strip():
        return []

    from .spacy_loader import get_nlp

    matcher, category_by_canonical = _get_matcher()
    nlp = get_nlp()
    doc = nlp(text[:100_000])  # guard against pathologically long CVs

    seen = set()
    found = []
    for match_id, start, end in matcher(doc):
        canonical = nlp.vocab.strings[match_id]
        if canonical in seen:
            continue
        seen.add(canonical)
        found.append({
            "skill_name": canonical.lower(),
            "category": category_by_canonical.get(canonical, ""),
        })
    return found
