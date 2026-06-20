import sqlite3
import os
from datetime import date, datetime, timezone

def _get_db_path():
    return os.environ.get("CARBONCOACH_DB_PATH", "carboncoach.db")


def _get_connection():
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            category TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            co2_kg REAL NOT NULL,
            logged_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            guest_name TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    _migrate_v1(conn)
    _migrate_v2(conn)


def _migrate_v1(conn):
    cur = conn.execute("PRAGMA table_info(activities)")
    cols = {r[1] for r in cur.fetchall()}
    if "user_id" not in cols:
        conn.execute("ALTER TABLE activities ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
    cur = conn.execute("PRAGMA table_info(messages)")
    cols = {r[1] for r in cur.fetchall()}
    if "user_id" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
    conn.commit()


def _migrate_v2(conn):
    cur = conn.execute("PRAGMA table_info(activities)")
    cols = {r[1] for r in cur.fetchall()}
    if "latitude" not in cols:
        conn.execute("ALTER TABLE activities ADD COLUMN latitude REAL")
        conn.execute("ALTER TABLE activities ADD COLUMN longitude REAL")
    conn.commit()


def create_session(guest_name):
    conn = _get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (guest_name, created_at) VALUES (?, ?)",
        (guest_name, now),
    )
    conn.commit()
    conn.close()


def session_exists(guest_name):
    conn = _get_connection()
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE guest_name = ?", (guest_name,)
    ).fetchone()
    conn.close()
    return row is not None


def get_all_sessions():
    conn = _get_connection()
    rows = conn.execute(
        "SELECT guest_name, created_at FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [{"guest_name": r["guest_name"], "created_at": r["created_at"]} for r in rows]


def save_activity(user_id, category, activity_type, quantity, co2_kg, lat=None, lng=None):
    conn = _get_connection()
    conn.execute(
        "INSERT INTO activities (user_id, category, activity_type, quantity, co2_kg, logged_at, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, category, activity_type, quantity, co2_kg, datetime.now(timezone.utc).isoformat(), lat, lng),
    )
    conn.commit()
    conn.close()


def save_message(user_id, role, content):
    conn = _get_connection()
    conn.execute(
        "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (user_id, role, content, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_recent_messages(user_id, limit=10):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def get_activities_since(user_id, since_date):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT category, activity_type, quantity, co2_kg, logged_at, latitude, longitude FROM activities WHERE user_id = ? AND logged_at >= ? ORDER BY logged_at",
        (user_id, since_date.isoformat()),
    ).fetchall()
    conn.close()
    return [
        {
            "category": r["category"],
            "activity_type": r["activity_type"],
            "quantity": r["quantity"],
            "co2_kg": r["co2_kg"],
            "logged_at": r["logged_at"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for r in rows
    ]


def get_today_activities(user_id):
    return get_activities_since(user_id, datetime.now(timezone.utc).date())


def get_all_activity_summary(user_id):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT category, SUM(co2_kg) as total_kg FROM activities WHERE user_id = ? GROUP BY category",
        (user_id,),
    ).fetchall()
    conn.close()
    return {r["category"]: round(r["total_kg"], 4) for r in rows}


def get_all_activities_csv(user_id):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT category, activity_type, quantity, co2_kg, logged_at, latitude, longitude FROM activities WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    conn.close()
    return [
        {
            "category": r["category"],
            "activity_type": r["activity_type"],
            "quantity": r["quantity"],
            "co2_kg": r["co2_kg"],
            "logged_at": r["logged_at"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for r in rows
    ]


def clear_session_data(user_id):
    conn = _get_connection()
    conn.execute("DELETE FROM activities WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM sessions WHERE guest_name = ?", (user_id,))
    conn.commit()
    conn.close()
