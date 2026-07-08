"""
Skill discovery: pulls candidate skill names from external/internal sources
and queues them for human review as PendingSkill rows, rather than writing
directly into SkillTaxonomy. Every candidate is checked against the existing
taxonomy first (ml.nlp.skill_dedup) so the moderation queue only ever shows
a reviewer something genuinely new -- or a genuine near-duplicate, flagged
as such so they can reject it in one click instead of creating a redundant
entry.
"""
import logging

from . import esco_client

logger = logging.getLogger(__name__)

# Broad domain queries used to sweep ESCO for skills adjacent to what the
# taxonomy already covers. Not exhaustive by design -- this is a discovery
# feed, not a bulk import; new domains can be added here as the platform's
# job-posting mix changes.
ESCO_SEED_QUERIES = [
    "programming", "software development", "cloud computing", "data analysis",
    "machine learning", "database management", "cybersecurity", "devops",
    "project management", "digital marketing", "sales", "accounting",
    "human resources", "customer service", "graphic design", "product management",
    "quality assurance", "network administration", "business analysis", "ux design",
]


def _create_pending_skill(*, proposed_name, source, source_detail, category="",
                           similar_skill=None, similarity_score=None, match_type="",
                           submitted_by=None):
    from apps.taxonomy.models import PendingSkill

    exists = PendingSkill.objects.filter(
        proposed_name__iexact=proposed_name, status=PendingSkill.Status.PENDING
    ).exists()
    if exists:
        return None

    return PendingSkill.objects.create(
        proposed_name=proposed_name,
        category=category,
        source=source,
        source_detail=source_detail,
        status=PendingSkill.Status.PENDING,
        similar_existing_skill=similar_skill,
        similarity_score=similarity_score,
        similarity_match_type=match_type,
        submitted_by=submitted_by,
    )


def sync_esco_skills(queries=None, limit_per_query: int = 10) -> dict:
    """Sweep ESCO for skill terms, queue anything not already covered.

    Returns a summary dict: {"queried": int, "seen": int, "queued": int,
    "duplicates_flagged": int, "skipped_existing_pending": int}.
    """
    from apps.taxonomy.models import PendingSkill
    from ml.nlp.skill_dedup import find_similar_skill

    queries = queries or ESCO_SEED_QUERIES
    seen_titles = set()
    stats = {"queried": 0, "seen": 0, "queued": 0, "duplicates_flagged": 0,
              "skipped_existing_pending": 0}

    for query in queries:
        stats["queried"] += 1
        results = esco_client.search_skills(query, limit=limit_per_query)
        for result in results:
            title = result["title"].strip()
            if not title or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())
            stats["seen"] += 1

            skill, score, match_type = find_similar_skill(title)
            if match_type == "exact":
                # Already in the taxonomy verbatim (or as a known alias) --
                # nothing to queue.
                continue

            created = _create_pending_skill(
                proposed_name=title,
                source=PendingSkill.Source.ESCO_SYNC,
                source_detail=result["uri"],
                similar_skill=skill,
                similarity_score=score,
                match_type=match_type or "",
            )
            if created is None:
                stats["skipped_existing_pending"] += 1
            else:
                stats["queued"] += 1
                if match_type:
                    stats["duplicates_flagged"] += 1

    logger.info("ESCO sync complete: %s", stats)
    return stats


def mine_corpus_skills(min_occurrences: int = 5, sample_size: int = 500) -> dict:
    """Scan recent job descriptions and candidate CV text for capitalized
    multi-word noun phrases that look like skill/technology names but aren't
    already in the taxonomy or PhraseMatcher vocabulary. Frequent recurring
    terms are queued for review -- infrequent ones are almost always noise
    (typos, company names) and are dropped.
    """
    from collections import Counter

    from apps.candidates.models import CandidateCV
    from apps.jobs.models import JobPost
    from apps.taxonomy.models import PendingSkill
    from ml.nlp.skill_dedup import find_similar_skill
    from ml.nlp.spacy_loader import get_nlp

    nlp = get_nlp()
    counter = Counter()

    texts = list(
        JobPost.objects.exclude(description="").order_by("-created_at")
        .values_list("description", flat=True)[:sample_size]
    )
    texts += list(
        CandidateCV.objects.exclude(raw_text="").order_by("-uploaded_at")
        .values_list("raw_text", flat=True)[:sample_size]
    )

    # Entity types that are never skill names -- company names, people,
    # locations. Noun chunks overlapping one of these spans are dropped so
    # "Lloyds Bank" / "Microsoft" don't get mistaken for tech/tool names.
    NON_SKILL_ENTITY_LABELS = {"ORG", "PERSON", "GPE", "LOC", "NORP", "FAC", "PRODUCT"}

    for text in texts:
        doc = nlp(text[:5000])
        blocked_spans = [
            (ent.start_char, ent.end_char)
            for ent in doc.ents
            if ent.label_ in NON_SKILL_ENTITY_LABELS
        ]
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip()
            words = phrase.split()
            # Heuristic: 1-3 words, title/upper-cased tokens (proper-noun-like
            # tech/tool names), no stray punctuation -- filters out generic
            # phrases like "the team" while keeping "Apache Kafka", "Tableau".
            if not (1 <= len(words) <= 3):
                continue
            if not all(w[0].isupper() for w in words if w[0].isalpha()):
                continue
            if len(phrase) < 3 or len(phrase) > 40:
                continue
            if any(chunk.start_char < end and chunk.end_char > start
                   for start, end in blocked_spans):
                continue
            # Sentence-initial capitalization (e.g. "This", "You", "Attention")
            # produces false positives that pass the uppercase check for the
            # wrong reason -- require every token to actually be a noun/proper
            # noun, not a pronoun/determiner that merely opened a sentence.
            if any(tok.pos_ not in ("NOUN", "PROPN") for tok in chunk):
                continue
            if all(tok.is_stop for tok in chunk):
                continue
            counter[phrase] += 1

    stats = {"candidates_scanned": len(texts), "phrases_seen": len(counter),
              "queued": 0, "skipped_existing_pending": 0}

    for phrase, count in counter.items():
        if count < min_occurrences:
            continue
        skill, score, match_type = find_similar_skill(phrase)
        if match_type == "exact":
            continue

        created = _create_pending_skill(
            proposed_name=phrase,
            source=PendingSkill.Source.CORPUS_MINING,
            source_detail=f"seen in {count} postings/CVs",
            similar_skill=skill,
            similarity_score=score,
            match_type=match_type or "",
        )
        if created is None:
            stats["skipped_existing_pending"] += 1
        else:
            stats["queued"] += 1

    logger.info("Corpus mining complete: %s", stats)
    return stats


def approve_pending_skill(pending_skill, reviewer=None, category=None):
    """Promote a PendingSkill to a real SkillTaxonomy entry (or, if it was
    flagged as a near-duplicate, merge it in as an alias instead of creating
    a redundant row)."""
    from django.utils import timezone

    from apps.taxonomy.models import PendingSkill, SkillTaxonomy
    from ml.nlp.skill_dedup import reload_embedding_cache
    from ml.nlp.skill_matcher import reload_matcher

    if pending_skill.similar_existing_skill_id:
        target = pending_skill.similar_existing_skill
        aliases = set(target.aliases or [])
        aliases.add(pending_skill.proposed_name)
        target.aliases = sorted(aliases)
        target.save(update_fields=["aliases"])
        result = target
    else:
        result = SkillTaxonomy.objects.create(
            name=pending_skill.proposed_name.lower(),
            canonical_name=pending_skill.proposed_name,
            category=category or pending_skill.category or "Uncategorized",
            aliases=[],
        )

    pending_skill.status = PendingSkill.Status.APPROVED
    pending_skill.reviewed_by = reviewer
    pending_skill.reviewed_at = timezone.now()
    pending_skill.save(update_fields=["status", "reviewed_by", "reviewed_at"])

    reload_matcher()
    reload_embedding_cache()
    return result


def reject_pending_skill(pending_skill, reviewer=None):
    from django.utils import timezone

    from apps.taxonomy.models import PendingSkill

    pending_skill.status = PendingSkill.Status.REJECTED
    pending_skill.reviewed_by = reviewer
    pending_skill.reviewed_at = timezone.now()
    pending_skill.save(update_fields=["status", "reviewed_by", "reviewed_at"])
