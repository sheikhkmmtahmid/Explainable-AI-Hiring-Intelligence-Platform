"""
Explanation generation service.
Runs both SHAP and LIME on the feature vector and combines them into
one unified explanation. Neither method name is exposed to the user.
"""
import logging
import numpy as np
from typing import Literal

logger = logging.getLogger(__name__)


def generate_explanation(match_result_id: int, method: str = "combined") -> "ExplanationReport":
    from apps.matching.models import MatchResult
    from .models import ExplanationReport
    from ml.matching.scorer import build_feature_vector
    from ml.explainability.shap_explainer import explain_match
    from ml.explainability.lime_explainer import explain_with_lime

    mr = MatchResult.objects.select_related("candidate", "job").get(id=match_result_id)
    candidate = mr.candidate
    job = mr.job

    candidate_skills = {s.lower() for s in candidate.skills.values_list("skill_name", flat=True)}
    job_required = {s.lower() for s in job.skill_requirements.filter(is_required=True).values_list("skill_name", flat=True)}
    job_preferred = {s.lower() for s in job.skill_requirements.filter(is_required=False).values_list("skill_name", flat=True)}

    matched_required = candidate_skills & job_required
    missing_required = job_required - candidate_skills

    # Build feature vector for ML explainers
    candidate_data = {
        "semantic_score": mr.semantic_score,
        "skills": list(candidate_skills),
        "years_of_experience": candidate.years_of_experience or 0,
        "highest_education": candidate.highest_education or "",
        "seniority_level": getattr(candidate, "seniority_level", "mid") or "mid",
        "remote_preference": getattr(candidate, "remote_preference", "flexible") or "flexible",
    }
    job_data = {
        "required_skills": list(job_required),
        "preferred_skills": list(job_preferred),
        "min_experience_years": _min_experience_years(job),
        "required_education": "bachelor",
        "experience_level": job.experience_level or "mid",
        "work_model": job.work_model or "onsite",
    }
    feature_vector = build_feature_vector(candidate_data, job_data)

    # Run SHAP
    shap_result = explain_match(feature_vector)
    shap_map = {item["feature"]: item["shap_value"] for item in shap_result["shap_values"]}

    # Run LIME
    lime_result = explain_with_lime(feature_vector)
    lime_map = {item["feature"]: item["lime_weight"] for item in lime_result["lime_values"]}

    # Combine: normalize each to [0,1] then average
    all_features = list(shap_map.keys())

    shap_vals = np.nan_to_num(
        np.array([shap_map[f] for f in all_features], dtype=np.float64), nan=0.0
    )
    lime_vals = np.nan_to_num(
        np.array([lime_map[f] for f in all_features], dtype=np.float64), nan=0.0
    )

    shap_max = np.abs(shap_vals).max() or 1.0
    lime_max = np.abs(lime_vals).max() or 1.0

    shap_norm = shap_vals / shap_max
    lime_norm = lime_vals / lime_max

    combined = (shap_norm * 0.6 + lime_norm * 0.4)

    DISPLAY_NAMES = {
        "semantic_similarity":    "profile alignment",
        "required_skill_overlap": "required skills",
        "preferred_skill_overlap":"preferred skills",
        "experience_ratio":       "experience",
        "education_match":        "education",
        "seniority_match":        "seniority",
        "location_compatibility": "location fit",
    }
    feature_importances = {
        DISPLAY_NAMES.get(f, f): round(float(combined[i]), 4)
        for i, f in enumerate(all_features)
    }

    FEATURE_LABELS = {
        "semantic_similarity":    "Strong profile alignment with job description",
        "required_skill_overlap": "Required skills matched",
        "preferred_skill_overlap":"Preferred skills matched",
        "experience_ratio":       "Years of experience",
        "education_match":        "Education level meets requirement",
        "seniority_match":        "Seniority level matches role",
        "location_compatibility": "Location / work model fit",
    }
    MISSING_LABELS = {
        "semantic_similarity":    "Low profile alignment with job description",
        "required_skill_overlap": "Missing required skills",
        "preferred_skill_overlap":"Missing preferred skills",
        "experience_ratio":       "Insufficient years of experience",
        "education_match":        "Education level below requirement",
        "seniority_match":        "Seniority level mismatch",
        "location_compatibility": "Location / work model mismatch",
    }

    SIGNIFICANCE_THRESHOLD = 0.08

    sorted_features = sorted(feature_importances.items(), key=lambda x: abs(x[1]), reverse=True)
    top_positive = [
        {"feature": FEATURE_LABELS.get(f, f.replace("_", " ")), "impact": round(v, 4), "direction": "positive"}
        for f, v in sorted_features if v >= SIGNIFICANCE_THRESHOLD
    ][:4]
    top_negative = [
        {"feature": MISSING_LABELS.get(f, f.replace("_", " ")), "impact": round(v, 4), "direction": "negative"}
        for f, v in sorted_features if v <= -SIGNIFICANCE_THRESHOLD
    ][:4]

    summary = _build_summary(mr, list(matched_required), list(missing_required), candidate.years_of_experience or 0)

    report, _ = ExplanationReport.objects.update_or_create(
        match_result=mr,
        defaults={
            "method": "combined",
            "feature_importances": feature_importances,
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "missing_skills": sorted(missing_required),
            "matching_skills": sorted(matched_required),
            "summary_text": summary,
        },
    )
    return report


def _min_experience_years(job) -> float:
    reqs = job.skill_requirements.filter(min_years__isnull=False)
    years = [r.min_years for r in reqs if r.min_years]
    return max(years) if years else 0


def _build_summary(mr, matched: list, missing: list, years_exp: float) -> str:
    parts = [
        f"Overall match score: {mr.overall_score:.1%}.",
        f"The candidate matches {len(matched)} required skill{'s' if len(matched) != 1 else ''}.",
    ]
    if missing:
        shown = ', '.join(sorted(missing)[:3])
        more = f" and {len(missing) - 3} more" if len(missing) > 3 else ""
        parts.append(f"Missing: {shown}{more}.")
    parts.append(
        f"Experience score: {mr.experience_score:.1%} | "
        f"Semantic alignment: {mr.semantic_score:.1%}."
    )
    return " ".join(parts)
