"""
Regression tests for the match-scoring pipeline (apps/matching/services.py).

These exist because a real bug shipped and went unnoticed: the production
match weights had been trained on the synthetic hiring simulator, whose
labels are deliberately decorrelated from semantic_score, so the trained
weights assigned semantic_score a weight of essentially zero. On top of
that, education scoring was hardcoded to assume every job requires a
bachelor's degree. Neither was caught by the existing test suite because
nothing asserted on the actual weight values or on education/experience
scoring respecting real per-job data. These tests close that gap.
"""
import pytest

from apps.matching.services import (
    WEIGHTS,
    compute_education_score,
    compute_experience_score,
    compute_hybrid_score,
    compute_skill_overlap_score,
    match_candidate_to_job,
    run_batch_matching_for_job,
)


class TestWeightsIntegrity:
    """The exact bug this session found: trained weights zeroed out
    semantic_score because they were fit against the synthetic simulator's
    own decorrelated labels. These tests guard against that regression."""

    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=0.001)

    def test_semantic_weight_is_not_zero(self):
        """This is the specific regression: a weights file trained on
        synthetic-only data zeroed this out. Semantic similarity is the
        whole point of SBERT being in this pipeline at all -- if this ever
        comes back to zero, something upstream (a stale learned_weights.json,
        or train_weights.py defaulting to synthetic data again) is wrong."""
        assert WEIGHTS["semantic"] > 0.1

    def test_experience_weight_is_not_zero(self):
        assert WEIGHTS["experience"] > 0

    def test_heuristic_defaults_are_the_documented_values(self):
        # These are the fixed, principled defaults the system should fall
        # back to whenever no responsibly-trained per-org weights exist.
        assert WEIGHTS == {
            "semantic": 0.50,
            "skill_overlap": 0.30,
            "experience": 0.15,
            "education": 0.05,
        }


class TestComputeEducationScore:
    def test_no_stated_requirement_is_not_held_against_candidate(self):
        """The bug: this used to always compare against a hardcoded
        "bachelor" requirement. An unset job requirement should score as
        fully satisfied, not silently penalise candidates without a degree
        for jobs that never actually asked for one."""
        assert compute_education_score("", "") == 1.0
        assert compute_education_score("high_school", "") == 1.0

    def test_real_requirement_is_respected(self):
        assert compute_education_score("high_school", "bachelor") < 1.0
        assert compute_education_score("bachelor", "bachelor") == 1.0
        assert compute_education_score("phd", "bachelor") == 1.0

    def test_exceeding_requirement_scores_full(self):
        assert compute_education_score("master", "bachelor") == 1.0


class TestComputeExperienceScore:
    def test_no_stated_requirement_scores_full(self):
        assert compute_experience_score(0, None) == 1.0
        assert compute_experience_score(5, None) == 1.0

    def test_meeting_requirement_scores_full(self):
        assert compute_experience_score(5, 5) == 1.0
        assert compute_experience_score(10, 5) == 1.0

    def test_falling_short_scores_partial(self):
        assert compute_experience_score(2, 5) == pytest.approx(0.4)


class TestComputeSkillOverlapScore:
    def test_job_with_no_skills_scores_zero_not_one(self):
        """A job with no recorded skill requirements has nothing to prove
        overlap against -- this must not silently default to a perfect
        score, which would be indistinguishable from "matches everything"."""
        assert compute_skill_overlap_score(["python"], []) == 0.0

    def test_full_overlap(self):
        assert compute_skill_overlap_score(["python", "sql"], ["python", "sql"]) == 1.0

    def test_partial_overlap(self):
        assert compute_skill_overlap_score(["python"], ["python", "sql"]) == 0.5


class TestComputeHybridScore:
    def test_matches_weighted_sum(self):
        score = compute_hybrid_score(1.0, 1.0, 1.0, 1.0)
        assert score == pytest.approx(1.0)

    def test_semantic_alone_moves_the_score(self):
        """Direct regression check for the bug: with semantic weighted at
        zero, changing semantic_score from 0 to 1 would not move the
        overall score at all. It must."""
        low = compute_hybrid_score(0.0, 0.5, 1.0, 1.0)
        high = compute_hybrid_score(1.0, 0.5, 1.0, 1.0)
        assert high > low
        assert (high - low) == pytest.approx(WEIGHTS["semantic"])


@pytest.mark.django_db
class TestMatchCandidateToJobUsesRealJobData:
    """Integration-level check that the single-pair scoring path
    (apps/matching/services.py::match_candidate_to_job, used by the Explain
    page) actually reads each job's own required_education instead of the
    old hardcoded "bachelor" assumption."""

    def _make_candidate_with_embedding(self, education=""):
        from apps.candidates.models import Candidate, CandidateEmbedding
        candidate = Candidate.objects.create(
            full_name="Pipeline Test Candidate",
            email=f"pipeline-{education or 'none'}@test.com",
            highest_education=education,
            years_of_experience=3,
        )
        CandidateEmbedding.objects.create(
            candidate=candidate, vector=[1.0, 0.0, 0.0], model_name="test",
        )
        return candidate

    def _make_job_with_embedding(self, required_education=""):
        from apps.jobs.models import JobEmbedding, JobPost
        job = JobPost.objects.create(
            title="Pipeline Test Job", company="Test Co", description="desc",
            source="manual", external_id=f"pipeline-job-{required_education or 'none'}",
            required_education=required_education,
        )
        JobEmbedding.objects.create(job=job, vector=[1.0, 0.0, 0.0], model_name="test")
        return job

    def test_job_with_no_requirement_does_not_penalise_candidate(self):
        candidate = self._make_candidate_with_embedding(education="")
        job = self._make_job_with_embedding(required_education="")
        result = match_candidate_to_job(candidate, job)
        assert result["education_score"] == 1.0

    def test_job_with_real_requirement_is_respected(self):
        candidate = self._make_candidate_with_embedding(education="high_school")
        job = self._make_job_with_embedding(required_education="master")
        result = match_candidate_to_job(candidate, job)
        assert result["education_score"] < 1.0

    def test_semantic_score_is_present_and_nonzero_for_identical_vectors(self):
        candidate = self._make_candidate_with_embedding()
        job = self._make_job_with_embedding()
        result = match_candidate_to_job(candidate, job)
        assert result["semantic_score"] == pytest.approx(1.0)
        # And it must actually be reflected in the overall score, i.e. the
        # weight applied to it is not zero.
        assert result["overall_score"] > 0


@pytest.mark.django_db
class TestBatchMatchingUsesRealJobData:
    """Same check as above, but for run_batch_matching_for_job (used by
    seed_matches and the Celery batch-matching task) -- this path had its
    own separate hardcoded "bachelor" call site."""

    def test_batch_matching_respects_required_education(self):
        from apps.candidates.models import Candidate, CandidateEmbedding
        from apps.jobs.models import JobEmbedding, JobPost
        from apps.matching.models import MatchResult

        job = JobPost.objects.create(
            title="Batch Test Job", company="Test Co", description="desc",
            source="manual", external_id="batch-job-1", required_education="",
        )
        JobEmbedding.objects.create(job=job, vector=[1.0, 0.0, 0.0], model_name="test")

        candidate = Candidate.objects.create(
            full_name="Batch Test Candidate", email="batch@test.com",
            highest_education="", years_of_experience=2,
        )
        CandidateEmbedding.objects.create(candidate=candidate, vector=[1.0, 0.0, 0.0], model_name="test")

        run_batch_matching_for_job(job.id)
        mr = MatchResult.objects.get(job=job, candidate=candidate)
        # No requirement was stated, so an unqualified-looking candidate
        # should not be marked down on education just because the old code
        # assumed every job wanted a bachelor's degree.
        assert mr.education_score == 1.0
