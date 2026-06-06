from __future__ import annotations

from collections import defaultdict

from app.config import settings
from app.feishu.client import FeishuClient
from app.modules.task_service import TaskService


class TaskReminderService:
    def __init__(self, feishu_client: FeishuClient | None = None, task_service: TaskService | None = None) -> None:
        self.feishu = feishu_client or FeishuClient()
        self.tasks = task_service or TaskService()

    async def remind_due_tasks(self, lookahead_days: int | None = None) -> dict[str, int]:
        days = settings.task_reminder_lookahead_days if lookahead_days is None else lookahead_days
        tasks = self.tasks.due_tasks_for_reminder(days)
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for task in tasks:
            grouped[task["user_id"]].append(task)

        reminded_task_ids: list[int] = []
        for user_id, user_tasks in grouped.items():
            await self.feishu.send_text(user_id, _format_reminder(user_tasks), receive_id_type="open_id")
            reminded_task_ids.extend(int(task["id"]) for task in user_tasks)
        self.tasks.mark_reminded(reminded_task_ids)
        return {"users": len(grouped), "tasks": len(reminded_task_ids)}


def _format_reminder(tasks: list[dict[str, str]]) -> str:
    lines = ["团务任务提醒："]
    for idx, task in enumerate(tasks, start=1):
        due = f"，截止：{task['due_at']}" if task.get("due_at") else ""
        lines.append(f"{idx}. {task['title']} [{task['status']}]{due}")
    lines.append("完成后请按支部要求反馈或更新状态。")
    return "\n".join(lines)
