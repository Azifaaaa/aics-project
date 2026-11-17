"""
CipherShield — SQLite Database Module
Manages optional analysis history and session statistics.
"""
import os
import sys
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, DATABASE_DIR, HISTORY_ENABLED


def get_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                label       TEXT    NOT NULL,
                confidence  REAL,
                has_url     INTEGER NOT NULL DEFAULT 0,
                url_count   INTEGER NOT NULL DEFAULT 0,
                model_name  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_stats (
                id              INTEGER PRIMARY KEY CHECK (id = 1),
                total_analysed  INTEGER NOT NULL DEFAULT 0,
                ham_count       INTEGER NOT NULL DEFAULT 0,
                spam_count      INTEGER NOT NULL DEFAULT 0,
                phishing_count  INTEGER NOT NULL DEFAULT 0,
                url_count_total INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Ensure a single stats row exists
        conn.execute("""
            INSERT OR IGNORE INTO session_stats
                (id, total_analysed, ham_count, spam_count, phishing_count, url_count_total)
            VALUES (1, 0, 0, 0, 0, 0)
        """)
        conn.commit()


def record_analysis(label: str, confidence: float, has_url: bool,
                    url_count: int, model_name: str = ""):
    """Insert a history record and update aggregate counters."""
    if not HISTORY_ENABLED:
        return
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_history
                    (timestamp, label, confidence, has_url, url_count, model_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds"),
                    label,
                    confidence,
                    int(has_url),
                    url_count,
                    model_name,
                ),
            )
            conn.execute(
                """
                UPDATE session_stats SET
                    total_analysed  = total_analysed + 1,
                    ham_count       = ham_count      + ?,
                    spam_count      = spam_count     + ?,
                    phishing_count  = phishing_count + ?,
                    url_count_total = url_count_total + ?
                WHERE id = 1
                """,
                (
                    1 if label == "ham" else 0,
                    1 if label == "spam" else 0,
                    1 if label == "phishing" else 0,
                    url_count,
                ),
            )
            conn.commit()
    except Exception as exc:
        print(f"[DB] record_analysis error: {exc}")


def get_history(limit: int = 50) -> list:
    """Return recent analysis records as a list of dicts."""
    if not HISTORY_ENABLED:
        return []
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, label, confidence, has_url, url_count, model_name
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_session_stats() -> dict:
    """Return aggregate session statistics."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_stats WHERE id = 1"
            ).fetchone()
        if row:
            return dict(row)
    except Exception:
        pass
    return {
        "total_analysed": 0,
        "ham_count": 0,
        "spam_count": 0,
        "phishing_count": 0,
        "url_count_total": 0,
    }


def clear_history():
    """Delete all history records and reset counters."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM analysis_history")
            conn.execute("""
                UPDATE session_stats SET
                    total_analysed=0, ham_count=0, spam_count=0,
                    phishing_count=0, url_count_total=0
                WHERE id=1
            """)
            conn.commit()
        return True
    except Exception as exc:
        print(f"[DB] clear_history error: {exc}")
        return False
