"""Tests for language routing helpers."""

from biai.ai.language import (
    detect_primary_language,
    is_language_compliant,
    normalize_language_enforcement_mode,
    normalize_response_language,
    response_language_instruction,
)


class TestLanguageUtils:
    def test_normalize_supported_languages(self):
        assert normalize_response_language("pl") == "pl"
        assert normalize_response_language("en") == "en"

    def test_normalize_fallback_to_polish(self):
        assert normalize_response_language("de") == "pl"
        assert normalize_response_language("") == "pl"

    def test_instruction_english(self):
        assert response_language_instruction("en") == "Respond strictly in English. Do not use Polish."

    def test_instruction_polish_default(self):
        assert response_language_instruction("pl") == "Odpowiadaj wylacznie po polsku. Nie uzywaj angielskiego."

    def test_normalize_language_enforcement_mode(self):
        assert normalize_language_enforcement_mode("strict") == "strict"
        assert normalize_language_enforcement_mode("best_effort") == "best_effort"
        assert normalize_language_enforcement_mode("random") == "strict"

    def test_detect_primary_language(self):
        assert detect_primary_language("To jest podsumowanie danych w tabeli.") == "pl"
        assert detect_primary_language("This is a summary of the query results.") == "en"

    def test_language_compliance(self):
        assert is_language_compliant("To jest podsumowanie danych.", "pl")
        assert not is_language_compliant("This is a summary.", "pl")
