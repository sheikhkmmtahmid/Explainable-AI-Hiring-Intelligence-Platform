"""
Advanced matching scorer using SBERT + feature engineering.
Used by apps.matching.services for ML-backed scoring.
"""
import numpy as np
from typing import Optional


def build_feature_vector(candidate_data: dict, job_data: dict) -> np.ndarray:
    """
    Build a numeric feature vector from candidate/job attributes.
    Used for SHAP-based explainability.
    """
    features = []

    # Semantic score (pre-computed cosine similarity)
    features.append(candidate_data.get("semantic_score", 0.0))

    # Skill overlap ratio
    c_skills = set(s.lower() for s in candidate_data.get("skills", []))
    j_required = set(s.lower() for s in job_data.get("required_skills", []))
    j_preferred = set(s.lower() for s in job_data.get("preferred_skills", []))
    req_overlap = len(c_skills & j_required) / max(len(j_required), 1)
    pref_overlap = len(c_skills & j_preferred) / max(len(j_preferred), 1)
    features.extend([req_overlap, pref_overlap])

    # Experience ratio
    c_exp = candidate_data.get("years_of_experience", 0)
    j_exp = job_data.get("min_experience_years", 0) or 0
    exp_ratio = min(c_exp / max(j_exp, 1), 1.5)
    features.append(exp_ratio)

    # Education match (ordinal encoding)
    edu_map = {"high_school": 1, "associate": 2, "bachelor": 3, "master": 4, "phd": 5}
    c_edu = edu_map.get(candidate_data.get("highest_education", ""), 0)
    j_edu = edu_map.get(job_data.get("required_education", "bachelor"), 3)
    features.append(int(c_edu >= j_edu))

    # Seniority match
    seniority_map = {"intern": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4, "principal": 5, "executive": 6}
    c_sen = seniority_map.get(candidate_data.get("seniority_level", "mid"), 2)
    j_sen = seniority_map.get(job_data.get("experience_level", "mid"), 2)
    features.append(1.0 - min(abs(c_sen - j_sen) / 6, 1.0))

    # Location match (remote-friendly)
    c_remote = candidate_data.get("remote_preference", "flexible")
    j_work_model = job_data.get("work_model", "onsite")
    location_match = _location_compat(c_remote, j_work_model)
    features.append(location_match)

    return np.array(features, dtype=np.float32)


def _location_compat(candidate_pref: str, job_model: str) -> float:
    matrix = {
        ("remote", "remote"): 1.0, ("remote", "hybrid"): 0.7, ("remote", "onsite"): 0.2,
        ("onsite", "onsite"): 1.0, ("onsite", "hybrid"): 0.7, ("onsite", "remote"): 0.5,
        ("hybrid", "hybrid"): 1.0, ("hybrid", "remote"): 0.8, ("hybrid", "onsite"): 0.8,
        ("flexible", "remote"): 1.0, ("flexible", "hybrid"): 1.0, ("flexible", "onsite"): 1.0,
    }
    return matrix.get((candidate_pref, job_model), 0.5)
