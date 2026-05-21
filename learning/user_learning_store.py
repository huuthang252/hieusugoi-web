"""
learning/user_learning_store.py
Persists user quiz attempts and weak-item tracking to a local SQLite database.

DB location (macOS): ~/Library/Application Support/Hieusugoi/user_learning.db

Public API:
  save_quiz_attempt(quiz_id, level, selected, correct, is_correct,
                    grammar_refs=(), vocab_refs=())
  get_db_path() -> Path
"""

from __future__ import annotations

import datetime
import os
import sqlite3
from pathlib import Path
from typing import Sequence

# ── DB path ───────────────────────────────────────────────────────────────────

def get_db_path() -> Path:
    from hieusugoi.config import get_app_data_dir
    return Path(get_app_data_dir()) / "user_learning.db"


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id         TEXT,
    level           TEXT,
    selected_answer INTEGER,
    correct_answer  INTEGER,
    is_correct      INTEGER,
    attempted_at    TEXT
);

CREATE TABLE IF NOT EXISTS weak_grammar (
    grammar_id    TEXT PRIMARY KEY,
    level         TEXT,
    wrong_count   INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    last_seen_at  TEXT
);

CREATE TABLE IF NOT EXISTS weak_vocabulary (
    vocab_id      TEXT PRIMARY KEY,
    level         TEXT,
    wrong_count   INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    last_seen_at  TEXT
);

CREATE TABLE IF NOT EXISTS daily_learning_stats (
    date             TEXT PRIMARY KEY,
    quiz_answered    INTEGER NOT NULL DEFAULT 0,
    quiz_correct     INTEGER NOT NULL DEFAULT 0,
    grammar_reviewed INTEGER NOT NULL DEFAULT 0,
    study_minutes    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS context_review_queue (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id      TEXT    NOT NULL,
    item_type    TEXT    NOT NULL,
    level        TEXT,
    source_text  TEXT,
    seen_count   INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT,
    created_at   TEXT,
    UNIQUE(item_id, item_type)
);
"""

# ── Connection (lazy, module-level singleton) ─────────────────────────────────

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    db = get_db_path()
    try:
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db), check_same_thread=False)
        conn.executescript(_DDL)
        conn.commit()
        _conn = conn
    except Exception as exc:
        raise RuntimeError(f"Cannot open user_learning.db: {exc}") from exc
    return _conn


# ── Public API ────────────────────────────────────────────────────────────────

def save_quiz_attempt(
    quiz_id: str,
    level: str,
    selected_answer: int,
    correct_answer: int,
    is_correct: bool,
    grammar_refs: Sequence[str] = (),
    vocab_refs: Sequence[str] = (),
) -> None:
    """Record a quiz answer and update weak-item counters.

    Errors are caught and printed as warnings — the app never crashes.
    """
    try:
        conn = _get_conn()
        now  = datetime.datetime.now().isoformat(timespec="seconds")

        # ── quiz_attempts ─────────────────────────────────────────────────
        conn.execute(
            "INSERT INTO quiz_attempts "
            "(quiz_id, level, selected_answer, correct_answer, is_correct, attempted_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (quiz_id, level, selected_answer, correct_answer, int(is_correct), now),
        )

        # ── weak counters ─────────────────────────────────────────────────
        d_correct = 1 if is_correct else 0
        d_wrong   = 0 if is_correct else 1

        for gid in grammar_refs:
            if not gid:
                continue
            conn.execute(
                """
                INSERT INTO weak_grammar (grammar_id, level, wrong_count, correct_count, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(grammar_id) DO UPDATE SET
                    wrong_count   = wrong_count   + excluded.wrong_count,
                    correct_count = correct_count + excluded.correct_count,
                    last_seen_at  = excluded.last_seen_at
                """,
                (gid, level, d_wrong, d_correct, now),
            )

        for vid in vocab_refs:
            if not vid:
                continue
            conn.execute(
                """
                INSERT INTO weak_vocabulary (vocab_id, level, wrong_count, correct_count, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(vocab_id) DO UPDATE SET
                    wrong_count   = wrong_count   + excluded.wrong_count,
                    correct_count = correct_count + excluded.correct_count,
                    last_seen_at  = excluded.last_seen_at
                """,
                (vid, level, d_wrong, d_correct, now),
            )

        conn.commit()
        print(f"[LEARNING] Saved quiz attempt: {quiz_id or '(no id)'} correct={is_correct}")

    except Exception as exc:
        print(f"[LEARNING] WARNING: failed to save quiz attempt — {exc}")


def update_daily_quiz_stats(is_correct: bool) -> None:
    """Increment today's quiz counters in daily_learning_stats."""
    try:
        conn  = _get_conn()
        today = datetime.date.today().isoformat()
        conn.execute(
            """
            INSERT INTO daily_learning_stats (date, quiz_answered, quiz_correct)
            VALUES (?, 1, ?)
            ON CONFLICT(date) DO UPDATE SET
                quiz_answered = quiz_answered + 1,
                quiz_correct  = quiz_correct  + excluded.quiz_correct
            """,
            (today, 1 if is_correct else 0),
        )
        conn.commit()
    except Exception as exc:
        print(f"[LEARNING] WARNING: update_daily_quiz_stats failed — {exc}")


def get_today_learning_stats() -> dict:
    """Return today's learning stats row as a dict (zeros if no row yet)."""
    _empty = {"quiz_answered": 0, "quiz_correct": 0,
              "grammar_reviewed": 0, "study_minutes": 0}
    try:
        conn  = _get_conn()
        today = datetime.date.today().isoformat()
        row   = conn.execute(
            "SELECT quiz_answered, quiz_correct, grammar_reviewed, study_minutes "
            "FROM daily_learning_stats WHERE date = ?",
            (today,),
        ).fetchone()
        if row:
            return {
                "quiz_answered":    row[0],
                "quiz_correct":     row[1],
                "grammar_reviewed": row[2],
                "study_minutes":    row[3],
            }
        return _empty
    except Exception as exc:
        print(f"[LEARNING] WARNING: get_today_learning_stats failed — {exc}")
        return _empty


def get_learning_streak() -> int:
    """Return the number of consecutive days (ending today or yesterday) with quiz activity."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT date FROM daily_learning_stats "
            "WHERE quiz_answered > 0 ORDER BY date DESC"
        ).fetchall()
        if not rows:
            return 0
        streak     = 0
        check_date = datetime.date.today()
        for (date_str,) in rows:
            row_date = datetime.date.fromisoformat(date_str)
            if row_date == check_date:
                streak    += 1
                check_date = check_date - datetime.timedelta(days=1)
            elif row_date < check_date:
                break  # gap — streak ends
        return streak
    except Exception as exc:
        print(f"[LEARNING] WARNING: get_learning_streak failed — {exc}")
        return 0


def save_context_detected_items(
    source_text: str,
    grammar_items: Sequence,
    vocab_items: Sequence,
) -> None:
    """Upsert detected grammar/vocabulary into context_review_queue.

    If the (item_id, item_type) pair already exists:
        seen_count +1, last_seen_at updated, source_text replaced.
    Otherwise a new row is inserted.
    """
    try:
        conn = _get_conn()
        now  = datetime.datetime.now().isoformat(timespec="seconds")

        for item in grammar_items:
            item_id = item.get("id", "")
            if not item_id:
                continue
            conn.execute(
                """
                INSERT INTO context_review_queue
                    (item_id, item_type, level, source_text, seen_count, last_seen_at, created_at)
                VALUES (?, 'grammar', ?, ?, 1, ?, ?)
                ON CONFLICT(item_id, item_type) DO UPDATE SET
                    seen_count   = seen_count + 1,
                    last_seen_at = excluded.last_seen_at,
                    source_text  = excluded.source_text
                """,
                (item_id, item.get("level", ""), source_text, now, now),
            )

        for item in vocab_items:
            item_id = item.get("id", "")
            if not item_id:
                continue
            conn.execute(
                """
                INSERT INTO context_review_queue
                    (item_id, item_type, level, source_text, seen_count, last_seen_at, created_at)
                VALUES (?, 'vocabulary', ?, ?, 1, ?, ?)
                ON CONFLICT(item_id, item_type) DO UPDATE SET
                    seen_count   = seen_count + 1,
                    last_seen_at = excluded.last_seen_at,
                    source_text  = excluded.source_text
                """,
                (item_id, item.get("level", ""), source_text, now, now),
            )

        conn.commit()
    except Exception as exc:
        print(f"[LEARNING] WARNING: save_context_detected_items failed — {exc}")


def get_recent_context_items(limit: int = 20) -> list[dict]:
    """Return the most recently seen items from context_review_queue."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT item_id, item_type, level, seen_count, last_seen_at
            FROM   context_review_queue
            ORDER  BY last_seen_at DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "item_id":      r[0],
                "item_type":    r[1],
                "level":        r[2],
                "seen_count":   r[3],
                "last_seen_at": r[4],
            }
            for r in rows
        ]
    except Exception as exc:
        print(f"[LEARNING] WARNING: get_recent_context_items failed — {exc}")
        return []
