"""Internationalization helpers for the Streamlit app."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import streamlit as st
import yaml

DEFAULT_LANGUAGE = "ja"
_LOCALES_DIR = Path(__file__).with_name("locales")
_LEGACY_FILE = Path(__file__).with_name("translations.yaml")


def _available_locale_files() -> List[Path]:
    """Return the list of available locale JSON files."""

    if not _LOCALES_DIR.exists():
        return []
    return sorted(p for p in _LOCALES_DIR.glob("*.json") if p.is_file())


@lru_cache()
def _load_locale(language: str) -> Dict[str, Any]:
    """Load a locale JSON file from disk."""

    locale_path = _LOCALES_DIR / f"{language}.json"
    if not locale_path.exists():
        return {}
    with locale_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


@lru_cache()
def _load_legacy_translations() -> Dict[str, Any]:
    """Load the legacy YAML translations for backward compatibility."""

    if not _LEGACY_FILE.exists():
        return {}
    with _LEGACY_FILE.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _resolve_from_dict(node: Dict[str, Any], key: str) -> Any:
    """Resolve a dotted key path inside a nested dictionary."""

    value: Any = node
    for part in key.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _resolve_from_locale(language: str, key: str) -> Any:
    """Fetch a translation value from a JSON locale file."""

    data = _load_locale(language)
    if not data:
        return None
    return _resolve_from_dict(data, key)


def _resolve_from_legacy(key: str) -> Any:
    """Fetch a translation value from the legacy YAML file."""

    legacy = _load_legacy_translations()
    if not legacy:
        return None
    return _resolve_from_dict(legacy, key)


def _fallback_sequence(preferred: str) -> Sequence[str]:
    """Return the sequence of languages to try for fallbacks."""

    seen = set()
    order = []
    for code in (preferred, DEFAULT_LANGUAGE, "en"):
        if code and code not in seen:
            order.append(code)
            seen.add(code)
    return order


def init_language(default: str = DEFAULT_LANGUAGE) -> str:
    """Ensure the session state has a language value."""

    available = get_available_languages()
    if default not in available and available:
        default = available[0]
    if "language" not in st.session_state:
        st.session_state["language"] = default
    return st.session_state["language"]


def get_current_language() -> str:
    """Return the current language stored in the session state."""

    lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    available = get_available_languages()
    if available and lang not in available:
        return available[0]
    return lang


def get_available_languages() -> List[str]:
    """Return the supported language codes detected in the locales directory."""

    locale_codes = [path.stem for path in _available_locale_files()]
    if locale_codes:
        return locale_codes

    # Fallback to the legacy YAML metadata
    data = _load_legacy_translations()
    languages = data.get("languages")
    if isinstance(languages, list):
        return [str(code) for code in languages if code]
    if isinstance(languages, dict):
        return [str(code) for code in languages.keys()]
    names = data.get("language_names")
    if isinstance(names, dict):
        return [str(code) for code in names.keys()]
    return [DEFAULT_LANGUAGE]


def translate(key: str, *, language: str | None = None, default: str | None = None) -> str:
    """Fetch a translated string with graceful fallbacks."""

    lang = language or get_current_language()

    for candidate in _fallback_sequence(lang):
        value = _resolve_from_locale(candidate, key)
        if isinstance(value, str):
            return value
        if value is not None:
            # Non-string values are unsupported in JSON locales; continue fallback.
            break

    legacy_value = _resolve_from_legacy(key)
    if isinstance(legacy_value, dict):
        for candidate in _fallback_sequence(lang):
            candidate_value = legacy_value.get(candidate)
            if isinstance(candidate_value, str):
                return candidate_value
        for candidate_value in legacy_value.values():
            if isinstance(candidate_value, str):
                return candidate_value
    elif isinstance(legacy_value, str):
        return legacy_value

    return default if default is not None else key


def language_name(code: str, *, language: str | None = None) -> str:
    """Return the localized display name for a language code."""

    return translate(f"language_names.{code}", language=language, default=code)


# Shorthand alias used in the app.
t = translate
