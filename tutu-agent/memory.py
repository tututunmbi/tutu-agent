"""
Persistent memory â stores conversations, decisions, insights.
Uses SQLite so it works on Railway with persistent storage.
"""
import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.getenv("MEMORY_DB_PATH", "tutu_memory.db")


class ConversationMemory:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'web',
                metadata TEXT DEFAULT '{}'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric TEXT NOT NULL,
                value TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS day_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                plan_text TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_message(self, role: str, content: str, source: str = "web", metadata: dict = None):
        """Save a conversation message."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (timestamp, role, content, source, metadata) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), role, content, source, json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()

    def get_recent_messages(self, limit: int = 20) -> list:
        """Get recent conversation messages for context."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT role, content, timestamp, source FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = c.fetchall()
        conn.close()
        # Reverse to get chronological order
        return [{"role": r[0], "content": r[1], "timestamp": r[2], "source": r[3]} for r in reversed(rows)]

    def save_insight(self, category: str, content: str, context: str = "", metadata: dict = None):
        """Save a key insight, decision, or commitment."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO insights (timestamp, category, content, context, metadata) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), category, content, context, json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()

    def get_insights(self, category: str = None, limit: int = 50) -> list:
        """Get stored insights, optionally filtered by category."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if category:
            c.execute(
                "SELECT category, content, context, timestamp FROM insights WHERE category = ? ORDER BY id DESC LIMIT ?",
                (category, limit)
            )
        else:
            c.execute(
                "SELECT category, content, context, timestamp FROM insights ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        rows = c.fetchall()
        conn.close()
        return [{"category": r[0], "content": r[1], "context": r[2], "timestamp": r[3]} for r in rows]

    def save_metric(self, metric: str, value: str, notes: str = ""):
        """Save a tracked metric (email subs, content count, etc)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO tracker (timestamp, metric, value, notes) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), metric, value, notes)
        )
        conn.commit()
        conn.close()

    def get_metrics(self, metric: str = None, limit: int = 30) -> list:
        """Get tracked metrics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if metric:
            c.execute(
                "SELECT metric, value, notes, timestamp FROM tracker WHERE metric = ? ORDER BY id DESC LIMIT ?",
                (metric, limit)
            )
        else:
            c.execute(
                "SELECT metric, value, notes, timestamp FROM tracker ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        rows = c.fetchall()
        conn.close()
        return [{"metric": r[0], "value": r[1], "notes": r[2], "timestamp": r[3]} for r in rows]

    def get_message_count(self) -> int:
        """Get total number of messages."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM messages")
        count = c.fetchone()[0]
        conn.close()
        return count

    def search_messages(self, query: str, limit: int = 10) -> list:
        """Search conversation history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT role, content, timestamp FROM messages WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        rows = c.fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

    # === DAY PLAN METHODS ===

    def save_day_plan(self, date: str, plan_text: str) -> bool:
        """Save or replace the day plan for a given date."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        # Deactivate any existing plan for this date
        c.execute(
            "UPDATE day_plans SET status = 'replaced', updated_at = ? WHERE date = ? AND status = 'active'",
            (now, date)
        )
        # Insert new plan
        c.execute(
            "INSERT INTO day_plans (date, plan_text, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (date, plan_text, now, now)
        )
        conn.commit()
        conn.close()
        return True

    def get_day_plan(self, date: str = None) -> dict:
        """Get the active day plan for a date (defaults to today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT plan_text, created_at, updated_at FROM day_plans WHERE date = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
            (date,)
        )
        row = c.fetchone()
        conn.close()
        if row:
            return {"date": date, "plan_text": row[0], "created_at": row[1], "updated_at": row[2]}
        return None

    def update_day_plan(self, date: str, plan_text: str) -> bool:
        """Update the active day plan for a date (used for recalibrations)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute(
            "UPDATE day_plans SET plan_text = ?, updated_at = ? WHERE date = ? AND status = 'active'",
            (plan_text, now, date)
        )
        updated = c.rowcount > 0
        conn.commit()
        conn.close()
        if not updated:
            # No existing plan, create one
            return self.save_day_plan(date, plan_text)
        return True
