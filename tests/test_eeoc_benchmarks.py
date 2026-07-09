"""Tests for ml/fairness/eeoc_benchmarks.py."""
import pytest

from ml.fairness.eeoc_benchmarks import compare_to_eeoc_benchmark, get_eeoc_benchmark


class TestGetEeocBenchmark:
    def test_gender_lookup(self):
        assert get_eeoc_benchmark("gender", "male") == 46.08
        assert get_eeoc_benchmark("gender", "female") == 44.35

    def test_gender_alias_lookup(self):
        assert get_eeoc_benchmark("gender", "Man") == 46.08
        assert get_eeoc_benchmark("gender", "F") == 44.35

    def test_ethnicity_lookup(self):
        assert get_eeoc_benchmark("ethnicity", "white") == 52.30
        assert get_eeoc_benchmark("ethnicity", "Black or African American") == 14.53

    def test_unsupported_attribute_returns_none(self):
        assert get_eeoc_benchmark("age_range", "25-34") is None
        assert get_eeoc_benchmark("disability_status", "true") is None

    def test_unknown_group_returns_none(self):
        assert get_eeoc_benchmark("gender", "nonbinary") is None
        assert get_eeoc_benchmark("ethnicity", "made up group") is None

    def test_empty_value_returns_none(self):
        assert get_eeoc_benchmark("gender", "") is None
        assert get_eeoc_benchmark("gender", "unknown") is None


class TestCompareToEeocBenchmark:
    def test_unsupported_attribute(self):
        result = compare_to_eeoc_benchmark("age_range", {"25-34": {"selection_rate": 0.5}})
        assert result["supported"] is False

    def test_matches_known_groups_only(self):
        subgroup_data = {
            "male": {"selection_rate": 0.60},
            "female": {"selection_rate": 0.40},
            "unknown": {"selection_rate": 0.10},
        }
        result = compare_to_eeoc_benchmark("gender", subgroup_data)
        assert result["supported"] is True
        assert set(result["groups"].keys()) == {"male", "female"}

    def test_gap_is_computed_correctly(self):
        subgroup_data = {"male": {"selection_rate": 0.60}}
        result = compare_to_eeoc_benchmark("gender", subgroup_data)
        group = result["groups"]["male"]
        assert group["organization_selection_rate_pct"] == 60.0
        assert group["eeoc_national_workforce_pct"] == 46.08
        assert group["gap_percentage_points"] == pytest.approx(13.92)

    def test_includes_source_citation(self):
        result = compare_to_eeoc_benchmark("gender", {"male": {"selection_rate": 0.5}})
        assert result["source_year"] == 2018
        assert "eeoc.gov" in result["source_url"]
