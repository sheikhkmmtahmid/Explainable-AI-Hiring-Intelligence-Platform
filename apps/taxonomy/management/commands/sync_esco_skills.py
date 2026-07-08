from django.core.management.base import BaseCommand

from apps.taxonomy.services import sync_esco_skills


class Command(BaseCommand):
    help = "Sweep the ESCO skill taxonomy for terms not yet covered by SkillTaxonomy, queueing them as PendingSkill for review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit-per-query", type=int, default=10,
            help="Max ESCO results to fetch per seed query (default: 10)",
        )

    def handle(self, *args, **options):
        stats = sync_esco_skills(limit_per_query=options["limit_per_query"])
        self.stdout.write(self.style.SUCCESS(
            f"ESCO sync done. Queries: {stats['queried']}, seen: {stats['seen']}, "
            f"queued: {stats['queued']} ({stats['duplicates_flagged']} flagged as possible "
            f"duplicates), skipped (already pending): {stats['skipped_existing_pending']}"
        ))
