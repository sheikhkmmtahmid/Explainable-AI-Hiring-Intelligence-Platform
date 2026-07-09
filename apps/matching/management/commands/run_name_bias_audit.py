"""
Runs the counterfactual name-bias probe (ml/fairness/name_bias_probe.py)
across a sample of real candidate/job pairs and reports the aggregate
white-vs-black average score gap -- a concrete, computed answer to "does
this platform's matching score shift based on name alone, holding the
resume completely fixed."

Usage:
    python manage.py run_name_bias_audit
    python manage.py run_name_bias_audit --sample 200
"""
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Audit SBERT match scores for name-based bias using a fixed-resume, name-swap probe"

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=200, help="Number of real candidate/job pairs to probe")

    def handle(self, *args, **options):
        from ml.fairness.name_bias_probe import run_name_bias_probe
        from apps.matching.models import MatchResult

        sample_size = options["sample"]

        # ORDER BY RAND() forces a full-table sort and blows TiDB's per-query
        # memory limit at this table size -- sample by shuffling a cheap,
        # indexed ID list in Python instead.
        import random

        candidate_ids = list(
            MatchResult.objects
            .filter(candidate__is_synthetic=False, job__is_synthetic=False)
            .exclude(candidate__raw_cv_text="")
            .values_list("id", flat=True)[:sample_size * 20]
        )
        random.shuffle(candidate_ids)
        pairs = list(
            MatchResult.objects
            .filter(id__in=candidate_ids[:sample_size])
            .select_related("candidate", "job", "job__embedding")
        )
        total = len(pairs)
        self.stdout.write(f"Probing {total} real candidate/job pairs...")

        if not total:
            self.stdout.write(self.style.WARNING("No eligible real candidate/job pairs with match results found."))
            return

        race_gaps = []
        score_ranges = []
        group_scores = {"white_female": [], "white_male": [], "black_female": [], "black_male": []}

        for i, mr in enumerate(pairs, start=1):
            try:
                job_vector = mr.job.embedding.vector
            except Exception:
                continue
            result = run_name_bias_probe(mr.candidate.raw_cv_text, job_vector)
            if "error" in result:
                continue
            if result["white_minus_black_gap"] is not None:
                race_gaps.append(result["white_minus_black_gap"])
            score_ranges.append(result["score_range"])
            for group, avg in result["group_average"].items():
                group_scores[group].append(avg)

            if i % 50 == 0:
                self.stdout.write(f"  {i}/{total}...")

        if not race_gaps:
            self.stdout.write(self.style.WARNING("No usable probe results."))
            return

        n = len(race_gaps)
        mean_gap = sum(race_gaps) / n
        mean_range = sum(score_ranges) / len(score_ranges)
        mean_by_group = {g: round(sum(v) / len(v), 4) for g, v in group_scores.items() if v}

        self.stdout.write(self.style.SUCCESS(f"\n=== Name Bias Audit ({n} probes) ==="))
        self.stdout.write(f"Mean group scores: {mean_by_group}")
        self.stdout.write(f"Mean white-minus-black score gap: {mean_gap:+.4f}")
        self.stdout.write(f"Mean score range across all 24 name variants per resume: {mean_range:.4f}")
        self.stdout.write(
            "\n(Positive gap = white-coded names scored higher on average, holding the resume fixed. "
            "A gap near zero means the match score is not meaningfully sensitive to name alone.)"
        )
