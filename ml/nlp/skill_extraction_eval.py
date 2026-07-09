"""
A small, honest, hand-annotated evaluation of the CV skill extraction
pipeline (spaCy + ml.nlp.skill_matcher) against real resumes.

Why this exists
----------------
Unlike the match-scoring classifier, skill extraction quality doesn't need
any hiring-outcome ground truth to check honestly -- it just needs a human
to read a real resume and compare what a person would call "the skills
mentioned" against what the pipeline actually extracted. That's what this
does.

Methodology
-----------
16 real candidates were sampled (random, seed=7) from imported real
datasets, excluding the OpenIntro audit study (its "resumes" are short
fabricated bio stubs by design, not full free-text CVs, so they aren't a
fair test of extraction on real resume prose). For each, the developer
read the candidate's full raw_cv_text and manually listed the skills a
recruiter would reasonably tag, using the platform's own canonical skill
vocabulary (the same short, lowercase phrases the extractor itself
produces, e.g. "sql", "project management", not hyper-specific product
names). That manual list is ANNOTATED_SKILLS below -- it is fixed, and is
the "ground truth" this script checks the live extractor against.

One candidate (id 272840, a construction worker resume) had no taxonomy
-style skill terms in the text at all; the extractor correctly returned
nothing for it. It's included for completeness but contributes 0/0 to
precision and recall (there's nothing to get right or wrong), so it's
excluded from the aggregate ratio, consistent with standard practice for
empty-ground-truth examples.

This is a small sample. It is not a claim about extraction accuracy across
this platform's full 13,000+ real candidates, and it isn't re-annotated
automatically if the underlying resumes change -- it's a fixed, reproducible
check against a fixed, honestly-sourced sample. Re-run it any time:

    python manage.py shell -c "from ml.nlp.skill_extraction_eval import run; run()"
"""

ANNOTATED_SKILLS = {
    272840: set(),  # construction worker -- no taxonomy-style skills stated
    241624: {"sales", "negotiation", "business development", "market research", "time management", "territory management", "customer service"},
    274003: {"java", "javascript", "sql", "excel", "elt/etl", "html"},
    211890: {"marketing", "sales"},
    240339: {"accounting", "linux", "sql", "sales", "budgeting"},
    240695: {"sales", "marketing", "communication", "customer service"},
    273526: {"data analysis", "elt/etl", "linux", "sql"},
    240103: {"project management", "customer service", "communication", "budgeting", "accounting", "negotiation", "public speaking", "marketing"},
    271052: {"leadership"},
    211713: {"sales", "marketing", "communication"},
    240561: {"sales", "leadership", "communication", "marketing"},
    274639: {"leadership", "project management", "budgeting"},
    274386: {"sql", "excel", "powerpoint", "project management", "data analysis", "budgeting", "marketing", "sales"},
    240297: {"accounting", "communication", "leadership", "marketing", "sales", "statistics"},
    271478: {"sql", "elt/etl"},
    240639: {"accounting", "budgeting", "sql", "sales"},
}


def run():
    """Compare ANNOTATED_SKILLS against the live extracted CandidateSkill
    rows for each candidate and print precision/recall/F1 plus the specific
    false positives and false negatives, so the numbers are inspectable,
    not just a summary statistic."""
    from apps.candidates.models import Candidate

    total_tp = total_fp = total_fn = 0
    per_candidate = []

    for candidate_id, truth in ANNOTATED_SKILLS.items():
        candidate = Candidate.objects.get(id=candidate_id)
        extracted = set(candidate.skills.values_list("skill_name", flat=True))

        tp = extracted & truth
        fp = extracted - truth
        fn = truth - extracted

        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)

        per_candidate.append({
            "candidate_id": candidate_id,
            "source": candidate.source,
            "ground_truth": sorted(truth),
            "extracted": sorted(extracted),
            "false_positives": sorted(fp),
            "false_negatives": sorted(fn),
        })

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else None
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None

    for row in per_candidate:
        print(f"candidate={row['candidate_id']} source={row['source']}")
        print(f"  ground truth: {row['ground_truth']}")
        print(f"  extracted:    {row['extracted']}")
        if row["false_positives"]:
            print(f"  FALSE POSITIVES: {row['false_positives']}")
        if row["false_negatives"]:
            print(f"  FALSE NEGATIVES: {row['false_negatives']}")

    print()
    print(f"n candidates: {len(ANNOTATED_SKILLS)} | true positives: {total_tp} | false positives: {total_fp} | false negatives: {total_fn}")
    print(f"precision: {precision:.4f} | recall: {recall:.4f} | F1: {f1:.4f}")

    return {
        "n_candidates": len(ANNOTATED_SKILLS),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
        "per_candidate": per_candidate,
    }
