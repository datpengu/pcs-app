"""Small SQLite persistence layer for people-counting history."""

import sqlite3
from datetime import datetime


class CounterStorage:
    def __init__(self, database_path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _create_tables(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS crossing_events (
                    id INTEGER PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('entered', 'exited')),
                    track_id INTEGER NOT NULL,
                    inside_count INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS counter_state (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );
                """
            )

    def record_crossing(self, event):
        occurred_at = datetime.now().astimezone().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO crossing_events
                    (occurred_at, direction, track_id, inside_count)
                VALUES (?, ?, ?, ?)
                """,
                (occurred_at, event["direction"], event["track_id"], event["inside"]),
            )
            connection.execute(
                """
                INSERT INTO counter_state (name, value) VALUES ('inside', ?)
                ON CONFLICT(name) DO UPDATE SET value = excluded.value
                """,
                (event["inside"],),
            )

    def restore_today(self):
        today = datetime.now().astimezone().date().isoformat()
        with self._connect() as connection:
            inside = connection.execute(
                "SELECT value FROM counter_state WHERE name = 'inside'"
            ).fetchone()
            totals = connection.execute(
                """
                SELECT
                    COALESCE(SUM(direction = 'entered'), 0),
                    COALESCE(SUM(direction = 'exited'), 0)
                FROM crossing_events
                WHERE substr(occurred_at, 1, 10) = ?
                """,
                (today,),
            ).fetchone()

        return {"inside": inside[0] if inside else 0, "entered": totals[0], "exited": totals[1]}

    def daily_history(self, days=14):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    substr(occurred_at, 1, 10) AS day,
                    SUM(direction = 'entered') AS entered,
                    SUM(direction = 'exited') AS exited
                FROM crossing_events
                GROUP BY day
                ORDER BY day DESC
                LIMIT ?
                """,
                (days,),
            ).fetchall()

        return [
            {"date": day, "entered": entered, "exited": exited}
            for day, entered, exited in rows
        ]
