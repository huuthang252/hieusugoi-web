"""
learning/jlpt_loader.py
Loads JLPT data from the nested dataset structure:

  data/jlpt/<LEVEL>/grammar/*.json
  data/jlpt/<LEVEL>/vocabulary/*.json
  data/jlpt/<LEVEL>/quiz/*.json

Public API:
  load_level_data(level)  -> {"grammar": [...], "vocabulary": [...], "quiz": [...]}
  sample_items(pool, n)   -> random sample of up to n items
  invalidate(level=None)  -> clear cache
"""

from __future__ import annotations

import json
import random
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).parent.parent / "data" / "jlpt"

LEVELS = ("N5", "N4", "N3", "N2", "N1")
CATEGORIES = ("grammar", "vocabulary", "quiz")

# ── In-memory cache: level → {grammar, vocabulary, quiz} ─────────────────────

_cache: dict[str, dict[str, list]] = {}


# ── Private helpers ───────────────────────────────────────────────────────────

def _load_category(level: str, category: str) -> list:
    """Merge all *.json files in data/jlpt/{level}/{category}/.

    Each file may contain a JSON array (list of items) or a single JSON object.
    Silently skips files that are unreadable or malformed.
    """
    cat_dir = _DATA_DIR / level / category
    items: list = []

    if not cat_dir.is_dir():
        return items

    for json_path in sorted(cat_dir.glob("*.json")):
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue  # malformed / unreadable — skip silently

        if isinstance(raw, list):
            items.extend(raw)
        elif isinstance(raw, dict) and raw:
            items.append(raw)
        # else: empty object or unexpected type — skip

    return items


# ── Public API ────────────────────────────────────────────────────────────────

def load_level_data(level: str, *, force: bool = False) -> dict[str, list]:
    """Return all grammar / vocabulary / quiz items for *level*.

    Results are cached after the first load.  Pass ``force=True`` to reload
    from disk (e.g. after the user updates a JSON file at runtime).

    Returns a dict with three guaranteed keys even if the files are missing:
        {"grammar": [], "vocabulary": [], "quiz": []}
    """
    if not force and level in _cache:
        return _cache[level]

    result: dict[str, list] = {
        "grammar":    _load_category(level, "grammar"),
        "vocabulary": _load_category(level, "vocabulary"),
        "quiz":       _load_category(level, "quiz"),
    }
    _cache[level] = result
    return result


def sample_items(pool: list, n: int) -> list:
    """Return up to *n* randomly chosen items from *pool* (no repeats)."""
    if not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


def has_data(level: str) -> bool:
    """Return True if the nested structure contains at least one item for *level*."""
    d = load_level_data(level)
    return bool(d["grammar"] or d["vocabulary"] or d["quiz"])


def invalidate(level: str | None = None) -> None:
    """Clear cached data.  Pass a level string to clear only that level,
    or None to clear the entire cache."""
    if level is not None:
        _cache.pop(level, None)
    else:
        _cache.clear()
