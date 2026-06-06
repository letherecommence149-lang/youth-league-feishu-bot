from __future__ import annotations

import sqlite3

from app.database import db_connection


class ActivityService:
    def signup(self, activity_name: str, user_id: str, user_name: str = "") -> str:
        if not activity_name.strip():
            activity_name = "春季团课学习活动"
        try:
            with db_connection() as conn:
                conn.execute(
                    "INSERT INTO activity_signups(activity_name, user_id, user_name) VALUES (?, ?, ?)",
                    (activity_name.strip(), user_id, user_name),
                )
        except sqlite3.IntegrityError:
            return f"你已经报名过「{activity_name}」了。"
        return f"已为你报名「{activity_name}」。活动通知和材料会在群内同步。"

    def count_signups(self, activity_name: str | None = None) -> int:
        with db_connection() as conn:
            if activity_name:
                row = conn.execute(
                    "SELECT COUNT(*) AS count FROM activity_signups WHERE activity_name = ?",
                    (activity_name,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS count FROM activity_signups").fetchone()
        return int(row["count"])

