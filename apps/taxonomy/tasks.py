import logging

from config.celery import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def sync_esco_skills_task(self):
    """Daily sweep of the ESCO skill taxonomy for terms not yet in our
    SkillTaxonomy -- queues candidates as PendingSkill for human review."""
    from apps.taxonomy.services import sync_esco_skills

    return sync_esco_skills()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def mine_corpus_skills_task(self):
    """Weekly scan of recent job/CV text for recurring skill-like terms not
    yet in our SkillTaxonomy -- queues candidates as PendingSkill."""
    from apps.taxonomy.services import mine_corpus_skills

    return mine_corpus_skills()
