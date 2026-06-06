from __future__ import annotations

from datetime import date, timedelta

from app.database import db_connection


class TaskService:
    def list_user_tasks(self, user_id: str) -> str:
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT title, status, due_at
                FROM tasks
                WHERE user_id = ?
                ORDER BY due_at ASC, id DESC
                LIMIT 10
                """,
                (user_id,),
            ).fetchall()
        if not rows:
            return "你当前没有待办任务。"
        lines = ["你的团务任务："]
        for idx, row in enumerate(rows, start=1):
            due = f"，截止：{row['due_at']}" if row["due_at"] else ""
            lines.append(f"{idx}. {row['title']} [{row['status']}]{due}")
        return "\n".join(lines)

    def due_tasks_for_reminder(self, lookahead_days: int = 3) -> list[dict[str, str]]:
        today = date.today()
        latest_due = today + timedelta(days=lookahead_days)
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, title, status, due_at, last_reminded_at
                FROM tasks
                WHERE user_id != ''
                  AND due_at != ''
                  AND date(due_at) <= date(?)
                  AND status NOT IN ('已完成', '完成', 'done', 'Done')
                ORDER BY due_at ASC, id DESC
                """,
                (latest_due.isoformat(),),
            ).fetchall()
        tasks: list[dict[str, str]] = []
        for row in rows:
            task = dict(row)
            if _should_remind(task, today):
                tasks.append({key: str(value) for key, value in task.items()})
        return tasks

    def mark_reminded(self, task_ids: list[int]) -> None:
        if not task_ids:
            return
        placeholders = ",".join("?" for _ in task_ids)
        with db_connection() as conn:
            conn.execute(
                f"UPDATE tasks SET last_reminded_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
                task_ids,
            )

    def complete_user_task(self, user_id: str, query: str) -> dict[str, str] | None:
        task = self.find_user_task(user_id, query)
        if task is None:
            return None
        self.mark_task_completed(int(task["id"]))
        task["status"] = "已完成"
        return task

    def find_user_task(self, user_id: str, query: str) -> dict[str, str] | None:
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, title, status, due_at, external_source, external_id
                FROM tasks
                WHERE user_id = ?
                ORDER BY due_at ASC, id DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
            row = _match_task(rows, query)
        if row is None:
            return None
        return {key: str(value) for key, value in dict(row).items()}

    def mark_task_completed(self, task_id: int) -> None:
        with db_connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = '已完成', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (task_id,),
            )


def _should_remind(task: dict[str, str], today: date) -> bool:
    reminded_at = task.get("last_reminded_at", "")
    if reminded_at.startswith(today.isoformat()):
        return False
    return True


def _match_task(rows, query: str):
    pending_rows = [row for row in rows if row["status"] not in {"已完成", "完成", "done", "Done"}]
    candidates = pending_rows or list(rows)
    text = query.strip()
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(candidates):
            return candidates[index]
        return None
    if text:
        for row in candidates:
            if text in row["title"]:
                return row
        return None
    if len(candidates) == 1:
        return candidates[0]
    return None
