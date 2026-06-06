from __future__ import annotations

from app.config import settings
from app.feishu.client import FeishuClient, FeishuClientError
from app.modules.bitable_sync import BitableSyncService
from app.modules.task_service import TaskService


class TaskCompletionService:
    def __init__(
        self,
        feishu_client: FeishuClient | None = None,
        task_service: TaskService | None = None,
    ) -> None:
        self.feishu = feishu_client or FeishuClient()
        self.tasks = task_service or TaskService()

    async def complete_task(self, user_id: str, query: str) -> str:
        task = self.tasks.find_user_task(user_id, query)
        if task is None:
            return "没有找到要完成的任务。可以发送「我的任务」查看任务列表，再发送「完成任务 任务名」或「完成任务 1」。"

        if task.get("external_source") == "feishu_bitable:tasks" and task.get("external_id"):
            app_token = await BitableSyncService(feishu_client=self.feishu)._app_token()
            try:
                await self.feishu.update_bitable_record(
                    app_token,
                    settings.feishu_bitable_tasks_table_id,
                    task["external_id"],
                    {"状态": "已完成"},
                )
            except FeishuClientError:
                return "已找到任务，但暂时不能写回多维表格。请管理员在开放平台开通「更新多维表格记录」权限后再试。"
        self.tasks.mark_task_completed(int(task["id"]))
        return f"已将任务标记为已完成：{task['title']}"
