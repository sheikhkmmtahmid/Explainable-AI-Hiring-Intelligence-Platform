"""
Counterfactual name-bias probe: holds a candidate's actual resume content
completely fixed and swaps ONLY the name attached to it, then measures
whether that alone moves the SBERT semantic match score against a job.

Why this exists: protected attributes (gender/ethnicity/age/disability) are
never fed into the matching model as direct inputs (verified -- see
ml/matching/scorer.py's build_feature_vector). But a resume's free text can
still carry indirect, name-based race/gender signal that SBERT's embedding
picks up on even though no explicit protected-attribute field was ever
touched -- this is the classic "proxy discrimination" failure mode audit
studies are designed to catch. This probe tests for it directly and
quantitatively instead of just asserting the model "doesn't see" protected
attributes.

The probe names are the real, most frequent first names actually used in
the Bertrand & Mullainathan (2004) resume-callback audit study -- pulled
directly from the imported dataset (see
apps/ingestion/management/commands/import_openintro_audit_study.py), not
invented. Same names the original published study used to establish
race/gender signal via first name alone.
"""
import logging

logger = logging.getLogger(__name__)

# The 6 most common first names per race x gender group in the actual
# Bertrand & Mullainathan (2004) dataset, verified by querying the imported
# data itself (see ml/fairness/name_bias_probe.py docstring).
PROBE_NAMES = {
    "white_female": ["Anne", "Allison", "Emily", "Kristen", "Jill", "Laurie"],
    "white_male":   ["Neil", "Todd", "Jay", "Matthew", "Brendan", "Brad"],
    "black_female": ["Tamika", "Latonya", "Latoya", "Ebony", "Tanisha", "Lakisha"],
    "black_male":   ["Tyrone", "Tremayne", "Rasheed", "Kareem", "Leroy", "Jamal"],
}


def _build_variant_text(resume_text: str, name: str) -> str:
    """Prepend a name header rather than trying to find-and-replace an
    existing name in the body -- works uniformly regardless of whether the
    original text happens to contain a literal name string."""
    return f"Name: {name}\n{resume_text}".strip()


def run_name_bias_probe(resume_text: str, job_vector: list[float]) -> dict:
    """
    For a fixed resume body and a fixed job, compute the SBERT match score
    under each of the 24 probe names (6 per group x 4 groups), changing
    nothing else. Returns per-group average scores and the max gap between
    any two groups -- a same-resume, name-only counterfactual fairness
    measurement.
    """
    from ml.embeddings.encoder import encode_batch, cosine_similarity_score

    if not resume_text or not resume_text.strip():
        return {"error": "empty resume text, nothing to probe"}

    all_names = [(group, name) for group, names in PROBE_NAMES.items() for name in names]
    variant_texts = [_build_variant_text(resume_text, name) for _, name in all_names]
    vectors = encode_batch(variant_texts, batch_size=32)

    scores_by_group = {group: [] for group in PROBE_NAMES}
    for (group, name), vec in zip(all_names, vectors):
        score = cosine_similarity_score(job_vector, vec.tolist())
        scores_by_group[group].append({"name": name, "score": round(score, 4)})

    group_avg = {
        group: round(sum(s["score"] for s in scores) / len(scores), 4)
        for group, scores in scores_by_group.items()
    }
    race_gap = round(
        max(group_avg["white_female"], group_avg["white_male"])
        - max(group_avg["black_female"], group_avg["black_male"]), 4
    ) if all(k in group_avg for k in ("white_female", "white_male", "black_female", "black_male")) else None
    all_scores = [s["score"] for scores in scores_by_group.values() for s in scores]

    return {
        "scores_by_group": scores_by_group,
        "group_average": group_avg,
        "white_minus_black_gap": race_gap,
        "max_score": round(max(all_scores), 4),
        "min_score": round(min(all_scores), 4),
        "score_range": round(max(all_scores) - min(all_scores), 4),
    }
