"""Tests for dialect-aware model profile suggestions."""

from biai.ai.model_profiles import get_model_profile


class TestModelProfiles:
    def test_oracle_profile(self):
        profile = get_model_profile("oracle")
        assert profile.db_type == "oracle"
        assert profile.label == "Oracle"
        assert profile.suggested_model != ""

    def test_postgresql_profile(self):
        profile = get_model_profile("postgresql")
        assert profile.db_type == "postgresql"
        assert profile.label == "PostgreSQL"
        assert profile.suggested_model != ""

    def test_profiles_use_shared_default_model(self):
        oracle_profile = get_model_profile("oracle")
        pg_profile = get_model_profile("postgresql")
        assert oracle_profile.suggested_model == pg_profile.suggested_model
