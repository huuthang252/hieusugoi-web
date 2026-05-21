"""
learning/weak_points_service.py
Reads weak grammar / vocabulary from the user learning DB.

Public API:
  get_top_weak_grammar(limit=10)    -> list[dict]
  get_top_weak_vocabulary(limit=10) -> list[dict]

Each dict has: grammar_id/vocab_id, level, wrong_count, correct_count.
Only items with wrong_count > 0 are returned.
"""

from __future__ import annotations

from typing import Any

# ── Shared DB connection via user_learning_store ──────────────────────────────

def _get_conn():
    from learning.user_learning_store import _get_conn as _store_conn
    return _store_conn()


# ── Public API ────────────────────────────────────────────────────────────────

def get_top_weak_grammar(limit: int = 10) -> list[dict[str, Any]]:
    """Return up to *limit* grammar items sorted by wrong_count DESC.

    Items with wrong_count == 0 are excluded.
    Returns [] if the DB is not available or has no data.
    """
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT grammar_id, level, wrong_count, correct_count
            FROM   weak_grammar
            WHERE  wrong_count > 0
            ORDER  BY wrong_count DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "grammar_id":    r[0],
                "level":         r[1],
                "wrong_count":   r[2],
                "correct_count": r[3],
            }
            for r in rows
        ]
    except Exception as exc:
        print(f"[LEARNING] WARNING: get_top_weak_grammar failed — {exc}")
        return []


def get_top_weak_vocabulary(limit: int = 10) -> list[dict[str, Any]]:
    """Return up to *limit* vocabulary items sorted by wrong_count DESC.

    Items with wrong_count == 0 are excluded.
    Returns [] if the DB is not available or has no data.
    """
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT vocab_id, level, wrong_count, correct_count
            FROM   weak_vocabulary
            WHERE  wrong_count > 0
            ORDER  BY wrong_count DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "vocab_id":      r[0],
                "level":         r[1],
                "wrong_count":   r[2],
                "correct_count": r[3],
            }
            for r in rows
        ]
    except Exception as exc:
        print(f"[LEARNING] WARNING: get_top_weak_vocabulary failed — {exc}")
        return []
