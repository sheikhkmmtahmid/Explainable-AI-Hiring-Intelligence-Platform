"""
Keeps MatchResult.hired in sync with real recruiter hiring decisions.

Application.status already has HIRED/REJECTED as terminal outcomes, keyed
by the same (candidate, job) pair as MatchResult. Without this signal,
MatchResult.hired stays null forever -- there is otherwise no path in the
app that ever sets it -- which means the XGBoost/GradientBoosting match
scorer (ml.matching.trainer) can never find labeled training data, no
matter how many applications get processed.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Application

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Application)
def sync_match_result_hired(sender, instance, **kwargs):
    from apps.matching.models import MatchResult

    if instance.status == Application.Status.HIRED:
        hired_value = True
    elif instance.status == Application.Status.REJECTED:
        hired_value = False
    else:
        return

    updated = MatchResult.objects.filter(
        candidate_id=instance.candidate_id, job_id=instance.job_id
    ).update(hired=hired_value)

    if updated:
        logger.info(
            "Synced MatchResult.hired=%s for candidate=%s job=%s (Application status=%s)",
            hired_value, instance.candidate_id, instance.job_id, instance.status,
        )
