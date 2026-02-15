"""Language helpers for LLM-generated natural language output."""

from __future__ import annotations

import re

DEFAULT_RESPONSE_LANGUAGE = "pl"
SUPPORTED_RESPONSE_LANGUAGES = {"pl", "en"}
DEFAULT_LANGUAGE_ENFORCEMENT_MODE = "strict"
SUPPORTED_LANGUAGE_ENFORCEMENT_MODES = {"strict", "best_effort"}

_POLISH_STOPWORDS = {
    "i", "oraz", "ale", "czy", "nie", "jest", "sa", "są", "dla", "z", "na", "w", "po", "to",
    "podsumowanie", "podsumowania", "dane", "danych", "wynik", "wyniki", "tabela", "zapytanie",
    "wierszy", "wiersze", "ktory", "która", "ktore", "które",
}
_ENGLISH_STOPWORDS = {
    "the", "and", "or", "but", "is", "are", "for", "with", "from", "in", "of",
    "summary", "data", "result", "results", "table", "query", "rows",
}


def normalize_response_language(language: str | None) -> str:
    """Normalize language code to one of the supported values."""
    value = (language or "").strip().lower()
    if value in SUPPORTED_RESPONSE_LANGUAGES:
        return value
    return DEFAULT_RESPONSE_LANGUAGE


def normalize_language_enforcement_mode(mode: str | None) -> str:
    """Normalize language enforcement mode."""
    value = (mode or "").strip().lower()
    if value in SUPPORTED_LANGUAGE_ENFORCEMENT_MODES:
        return value
    return DEFAULT_LANGUAGE_ENFORCEMENT_MODE


def response_language_instruction(language: str | None) -> str:
    """Return a prompt instruction for the selected response language."""
    normalized = normalize_response_language(language)
    if normalized == "en":
        return "Respond strictly in English. Do not use Polish."
    return "Odpowiadaj wylacznie po polsku. Nie uzywaj angielskiego."


def response_language_system_instruction(language: str | None) -> str:
    """Return a strict system-level language instruction for Ollama generate()."""
    normalized = normalize_response_language(language)
    if normalized == "en":
        return (
            "You are a business data assistant. Reply only in English. "
            "Do not output Polish words. Do not output XML/HTML tags."
        )
    return (
        "Jestes asystentem danych biznesowych. Odpowiadaj tylko po polsku. "
        "Nie uzywaj angielskich zdan. Nie uzywaj znacznikow XML/HTML."
    )


def detect_primary_language(text: str | None) -> str:
    """Detect the dominant language in free-text output."""
    if not text:
        return "unknown"

    lowered = text.lower()
    tokens = re.findall(r"[a-zA-Ząćęłńóśźż]+", lowered)
    if not tokens:
        return "unknown"

    score_pl = 0
    score_en = 0

    # Polish diacritics are a strong language signal.
    diacritics = len(re.findall(r"[ąćęłńóśźż]", lowered))
    score_pl += min(diacritics * 2, 8)

    for token in tokens:
        if token in _POLISH_STOPWORDS:
            score_pl += 1
        if token in _ENGLISH_STOPWORDS:
            score_en += 1

    # Resolve weak/mixed signals conservatively.
    if score_pl == 0 and score_en == 0:
        return "unknown"
    if score_pl >= score_en + 1:
        return "pl"
    if score_en >= score_pl + 1:
        return "en"
    return "unknown"


def is_language_compliant(text: str | None, target_language: str | None) -> bool:
    """Check if output language matches selected response language."""
    target = normalize_response_language(target_language)
    detected = detect_primary_language(text)
    if detected == "unknown":
        # Allow very short/mostly numeric outputs.
        letters = len(re.findall(r"[A-Za-ząćęłńóśźż]", text or ""))
        return letters < 25
    return detected == target
