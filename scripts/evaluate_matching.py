"""
Evaluate the matching system against synthetic ground truth labels.

Metrics computed
----------------
  Precision@K   — of the top-K ranked candidates, what fraction are truly relevant?
  Recall@K      — of all relevant candidates, what fraction appear in the top-K?
  NDCG@K        — Normalised Discounted Cumulative Gain (position-sensitive ranking quality)
  MRR           — Mean Reciprocal Rank (where does the first relevant result appear?)
  AUC-ROC       — overall discrimination power of the match score

  Per-group metrics:
    The above metrics are also broken down by protected attribute groups
    so you can surface ranking quality disparities across demographics.

Ground truth
------------
  A candidate–job pair is "relevant" if the synthetic application status is
  'shortlisted', 'interview', 'offer', or 'hired'.

Usage
-----
    python scripts/evaluate_matching.py --job-id 1
    python scripts/evaluate_matching.py --job-id 1 --k 10 --k 20 --k 50
    python scripts/evaluate_matching.py --all-jobs --k 10
    python scripts/evaluate_matching.py --all-jobs --output results/eval.json
"""

import argparse
import json
import logging
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RELEVANT_STATUSES = {"shortlisted", "interview", "offer", "hired"}
PROTECTED_ATTRIBUTES = ["gender", "age_range", "ethnicity"]


# ──────────────────────────────────────────────────────────────────────────────
# Core metric functions
# ──────────────────────────────────────────────────────────────────────────────

def precision_at_k(ranked_relevant: list[bool], k: int) -> float:
    """Fraction of top-K items that are relevant."""
    if k == 0:
        return 0.0
    top_k = ranked_relevant[:k]
    return sum(top_k) / k


def recall_at_k(ranked_relevant: list[bool], total_relevant: int, k: int) -> float:
    """Fraction of all relevant items appearing in top-K."""
    if total_relevant == 0:
        return 0.0
    top_k = ranked_relevant[:k]
    return sum(top_k) / total_relevant


def dcg_at_k(ranked_relevant: list[bool], k: int) -> float:
    """Discounted Cumulative Gain at K."""
    score = 0.0
    for i, rel in enumerate(ranked_relevant[:k], start=1):
        if rel:
            score += 1.0 / math.log2(i + 1)
    return score


def ndcg_at_k(ranked_relevant: list[bool], total_relevant: int, k: int) -> float:
    """Normalised DCG at K. Ideal DCG assumes all relevant items ranked first."""
    actual_dcg = dcg_at_k(ranked_relevant, k)
    # Ideal: all relevant items at the top
    ideal = [True] * min(total_relevant, k) + [False] * max(0, k - total_relevant)
    ideal_dcg = dcg_at_k(ideal, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def mean_reciprocal_rank(ranked_relevant: list[bool]) -> float:
    """Position of first relevant result (1-indexed)."""
    for i, rel in enumerate(ranked_relevant, start=1):
        if rel:
            return 1.0 / i
    return 0.0


def auc_roc(scores: list[float], labels: list[int]) -> float:
    """Simple AUC-ROC using the Wilcoxon–Mann–Whitney statistic."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return 0.5
    concordant = sum(1 for p in pos for n in neg if p > n)
    tied = sum(1 for p in pos for n in neg if p == n)
    total = len(pos) * len(neg)
    return (concordant + 0.5 * tied) / total


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation engine
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_job(job_id: int, k_values: list[int]) -> dict:
    from apps.applications.models import Application
    from apps.matching.models import MatchResult

    # Ground truth: which candidates are relevant for this job?
    relevant_candidate_ids = set(
        Application.objects.filter(
            job_id=job_id,
            status__in=RELEVANT_STATUSES,
            is_synthetic=True,
        ).values_list("candidate_id", flat=True)
    )

    # Model rankings: MatchResult ordered by overall_score descending
    match_results = list(
        MatchResult.objects.filter(job_id=job_id)
        .select_related("candidate")
        .order_by("-overall_score")
    )

    if not match_results:
        logger.warning("No match results for job %d. Run matching first.", job_id)
        return {}

    if not relevant_candidate_ids:
        logger.warning("No synthetic ground truth for job %d. Generate applications first.", job_id)
        return {}

    ranked_relevant = [mr.candidate_id in relevant_candidate_ids for mr in match_results]
    scores = [mr.overall_score for mr in match_results]
    labels = [1 if r else 0 for r in ranked_relevant]
    total_relevant = len(relevant_candidate_ids)

    metrics = {
        "job_id": job_id,
        "total_candidates_ranked": len(match_results),
        "total_relevant": total_relevant,
        "mrr": round(mean_reciprocal_rank(ranked_relevant), 4),
        "auc_roc": round(auc_roc(scores, labels), 4),
    }

    for k in k_values:
        metrics[f"precision@{k}"] = round(precision_at_k(ranked_relevant, k), 4)
        metrics[f"recall@{k}"] = round(recall_at_k(ranked_relevant, total_relevant, k), 4)
        metrics[f"ndcg@{k}"] = round(ndcg_at_k(ranked_relevant, total_relevant, k), 4)

    # Per-group breakdown
    group_metrics = _per_group_metrics(match_results, relevant_candidate_ids, k_values)
    metrics["per_group"] = group_metrics

    return metrics


def _per_group_metrics(match_results, relevant_ids: set, k_values: list[int]) -> dict:
    """Break down ranking quality by protected attribute groups."""
    from apps.candidates.models import Candidate

    candidate_attrs = {
        c.id: {attr: getattr(c, attr, None) for attr in PROTECTED_ATTRIBUTES}
        for c in Candidate.objects.filter(
            id__in=[mr.candidate_id for mr in match_results]
        )
    }

    per_group: dict = {}

    for attr in PROTECTED_ATTRIBUTES:
        groups: dict[str, list] = defaultdict(list)
        for mr in match_results:
            group_val = (candidate_attrs.get(mr.candidate_id) or {}).get(attr) or "unknown"
            groups[group_val].append(mr)

        per_group[attr] = {}
        for group_val, group_results in groups.items():
            group_relevant = [mr.candidate_id in relevant_ids for mr in group_results]
            total_rel = sum(group_relevant)
            group_scores = [mr.overall_score for mr in group_results]
            group_labels = [1 if r else 0 for r in group_relevant]

            g_metrics = {
                "count": len(group_results),
                "relevant": total_rel,
                "mrr": round(mean_reciprocal_rank(group_relevant), 4),
                "auc_roc": round(auc_roc(group_scores, group_labels), 4),
            }
            for k in k_values:
                g_metrics[f"ndcg@{k}"] = round(
                    ndcg_at_k(group_relevant, total_rel, k), 4
                )
            per_group[attr][str(group_val)] = g_metrics

    return per_group


def evaluate_all_jobs(k_values: list[int]) -> list[dict]:
    from apps.jobs.models import JobPost

    job_ids = list(
        JobPost.objects.filter(is_synthetic=True).values_list("id", flat=True)
    )
    logger.info("Evaluating %d synthetic jobs...", len(job_ids))
    all_results = []
    for job_id in job_ids:
        result = evaluate_job(job_id, k_values)
        if result:
            all_results.append(result)

    return all_results


def aggregate_results(results: list[dict], k_values: list[int]) -> dict:
    """Macro-average all per-job metrics into a single summary."""
    if not results:
        return {}

    summary: dict = {"jobs_evaluated": len(results)}
    metric_keys = ["mrr", "auc_roc"] + [
        f"{m}@{k}" for m in ("precision", "recall", "ndcg") for k in k_values
    ]
    for key in metric_keys:
        vals = [r[key] for r in results if key in r]
        summary[key] = round(sum(vals) / len(vals), 4) if vals else None

    return summary


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate HiringAI matching quality against synthetic ground truth"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--job-id", type=int, help="Evaluate a single job")
    group.add_argument("--all-jobs", action="store_true", help="Evaluate all synthetic jobs")
    parser.add_argument(
        "--k",
        type=int,
        action="append",
        dest="k_values",
        default=[],
        help="K value for P@K / R@K / NDCG@K (can be repeated, e.g. --k 5 --k 10 --k 20)",
    )
    parser.add_argument("--output", help="Save results as JSON to this path")
    args = parser.parse_args()

    k_values = args.k_values or [5, 10, 20]

    if args.job_id:
        result = evaluate_job(args.job_id, k_values)
        if not result:
            logger.error("No results returned for job %d.", args.job_id)
            sys.exit(1)
        _print_result(result, k_values)
        if args.output:
            _save_output([result], args.output)
    else:
        results = evaluate_all_jobs(k_values)
        summary = aggregate_results(results, k_values)
        logger.info("\n=== Macro-Averaged Summary ===")
        for k, v in summary.items():
            logger.info("  %-20s %s", k, v)
        if args.output:
            _save_output({"summary": summary, "per_job": results}, args.output)


def _print_result(result: dict, k_values: list[int]) -> None:
    logger.info("\n=== Job %d ===", result["job_id"])
    logger.info("  Ranked: %d  |  Relevant: %d", result["total_candidates_ranked"], result["total_relevant"])
    logger.info("  MRR: %.4f  |  AUC-ROC: %.4f", result["mrr"], result["auc_roc"])
    for k in k_values:
        logger.info(
            "  @%-4d  P=%.4f  R=%.4f  NDCG=%.4f",
            k, result.get(f"precision@{k}", 0),
            result.get(f"recall@{k}", 0),
            result.get(f"ndcg@{k}", 0),
        )


def _save_output(data: dict | list, path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Results saved to %s", out)


if __name__ == "__main__":
    main()
