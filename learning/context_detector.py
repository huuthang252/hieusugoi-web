"""
learning/context_detector.py
Detects JLPT grammar and vocabulary items in a given Japanese text.

Uses simple substring matching against each item's search_forms field.
Falls back to pattern (grammar) or word (vocabulary) when search_forms is absent.

Public API:
  detect_grammar(text, grammar_items, max_results=5)   -> list[dict]
  detect_vocabulary(text, vocab_items, max_results=5)  -> list[dict]
"""

from __future__ import annotations

from typing import Any


def detect_grammar(
    text: str,
    grammar_items: list[dict[str, Any]],
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Return up to *max_results* grammar items whose forms appear in *text*.

    Search order: search_forms list first; falls back to the pattern string
    with leading 〜/～ stripped.  Items are deduplicated by id.
    """
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for item in grammar_items:
        if len(results) >= max_results:
            break
        gid = item.get("id", "")
        if gid in seen:
            continue

        forms: list[str] = item.get("search_forms", [])
        if not forms:
            raw = item.get("pattern", "")
            clean = raw.lstrip("〜～")
            forms = [clean] if clean else []

        for form in forms:
            if form and form in text:
                seen.add(gid)
                results.append(item)
                break

    return results


def detect_vocabulary(
    text: str,
    vocab_items: list[dict[str, Any]],
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Return up to *max_results* vocabulary items whose forms appear in *text*.

    Search order: search_forms list first; falls back to word / kanji field.
    Items are deduplicated by id.
    """
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for item in vocab_items:
        if len(results) >= max_results:
            break
        vid = item.get("id", "")
        if vid in seen:
            continue

        forms: list[str] = item.get("search_forms", [])
        if not forms:
            word = item.get("word", item.get("kanji", ""))
            forms = [word] if word else []

        for form in forms:
            if form and form in text:
                seen.add(vid)
                results.append(item)
                break

    return results
