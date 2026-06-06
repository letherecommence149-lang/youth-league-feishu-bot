from __future__ import annotations

from datetime import date, timedelta

from app.database import db_connection, init_db
from app.modules.task_service import TaskService
from app.config import settings


def test_due_tasks_for_reminder_filters_completed_and_far_future(tmp_path):
    db_path = tmp_path / "bot.sqlite3"
    original_db_path = settings.database_path
    object.__setattr__(settings, "database_path", db_path)
    try:
        init_db()
        today = date.today()
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO tasks(user_id, title, status, due_at) VALUES (?, ?, ?, ?)",
                ("ou_1", "临近任务", "待完成", (today + timedelta(days=1)).isoformat()),
            )
            conn.execute(
                "INSERT INTO tasks(user_id, title, status, due_at) VALUES (?, ?, ?, ?)",
                ("ou_1", "已完成任务", "已完成", today.isoformat()),
            )
            conn.execute(
                "INSERT INTO tasks(user_id, title, status, due_at) VALUES (?, ?, ?, ?)",
                ("ou_1", "远期任务", "待完成", (today + timedelta(days=10)).isoformat()),
            )

        tasks = TaskService().due_tasks_for_reminder(lookahead_days=3)

        assert [task["title"] for task in tasks] == ["临近任务"]
    finally:
        object.__setattr__(settings, "database_path", original_db_path)


def test_complete_user_task_marks_matching_task_done(tmp_path):
    db_path = tmp_path / "bot.sqlite3"
    original_db_path = settings.database_path
    object.__setattr__(settings, "database_path", db_path)
    try:
        init_db()
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO tasks(user_id, title, status, due_at) VALUES (?, ?, ?, ?)",
                ("ou_1", "bot开发", "未完成", "2026-06-04"),
            )

        task = TaskService().complete_user_task("ou_1", "bot")

        assert task is not None
        assert task["title"] == "bot开发"
        with db_connection() as conn:
            status = conn.execute("SELECT status FROM tasks").fetchone()["status"]
        assert status == "已完成"
    finally:
        object.__setattr__(settings, "database_path", original_db_path)
