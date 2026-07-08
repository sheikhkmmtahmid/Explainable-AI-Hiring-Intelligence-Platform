from django.core.management.base import BaseCommand

from apps.taxonomy.services import mine_corpus_skills


class Command(BaseCommand):
    help = "Scan recent job descriptions and CV text for recurring skill-like terms not yet in SkillTaxonomy, queueing them as PendingSkill for review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-occurrences", type=int, default=5,
            help="Minimum number of postings/CVs a phrase must appear in to be queued (default: 5)",
        )
        parser.add_argument(
            "--sample-size", type=int, default=500,
            help="Max job descriptions / CVs to scan (default: 500 each)",
        )

    def handle(self, *args, **options):
        stats = mine_corpus_skills(
            min_occurrences=options["min_occurrences"], sample_size=options["sample_size"]
        )
        self.stdout.write(self.style.SUCCESS(
            f"Corpus mining done. Scanned: {stats['candidates_scanned']}, "
            f"distinct phrases seen: {stats['phrases_seen']}, queued: {stats['queued']}, "
            f"skipped (already pending): {stats['skipped_existing_pending']}"
        ))
