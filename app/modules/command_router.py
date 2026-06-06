from __future__ import annotations

from dataclasses import dataclass

from app.database import db_connection
from app.feishu.events import IncomingMessage
from app.modules.activity_service import ActivityService
from app.modules.material_service import MaterialService, format_materials
from app.modules.qa_service import QaService
from app.modules.report_service import ReportService
from app.modules.task_service import TaskService


HELP_TEXT = """智慧团建一键学 Bot 可用指令：
1. 帮助：查看指令
2. 搜索 关键词：检索学习资料
3. 本周学习：获取本周推荐学习材料
4. 活动报名 活动名称：报名团支部活动
5. 我的任务：查看个人待办
6. 完成任务 任务名/序号：提交任务完成状态
7. 周报：查看团务数据概览
8. 我的ID：查看自己的飞书 open_id，便于管理员分配任务
也可以直接提问，例如：团课怎么补？"""


@dataclass(frozen=True)
class BotReply:
    text: str
    command: str


class CommandRouter:
    def __init__(
        self,
        material_service: MaterialService | None = None,
        qa_service: QaService | None = None,
        activity_service: ActivityService | None = None,
        task_service: TaskService | None = None,
        report_service: ReportService | None = None,
    ) -> None:
        self.materials = material_service or MaterialService()
        self.qa = qa_service or QaService()
        self.activities = activity_service or ActivityService()
        self.tasks = task_service or TaskService()
        self.reports = report_service or ReportService()

    def handle(self, message: IncomingMessage) -> BotReply:
        text = message.text.strip()
        command = self._command_name(text)
        self._log_interaction(message, command)

        if not text or text in {"帮助", "help", "/help"}:
            return BotReply(HELP_TEXT, "帮助")

        if text.startswith(("搜索", "查找", "资料")):
            query = self._strip_prefix(text, ("搜索", "查找", "资料"))
            return BotReply(format_materials(self.materials.search(query)), "搜索")

        if text in {"本周学习", "本周资料", "学习材料"}:
            return BotReply(format_materials(self.materials.weekly_materials()), "本周学习")

        if text.startswith(("活动报名", "报名")):
            activity_name = self._strip_prefix(text, ("活动报名", "报名"))
            return BotReply(self.activities.signup(activity_name, message.user_id, message.user_name), "活动报名")

        if text in {"我的任务", "待办", "任务"}:
            return BotReply(self.tasks.list_user_tasks(message.user_id), "我的任务")

        if text in {"我的ID", "我的id", "open_id", "OpenID"}:
            return BotReply(f"你的飞书 open_id 是：{message.user_id}", "我的ID")

        if text in {"周报", "团务周报", "数据统计"}:
            return BotReply(self.reports.weekly_report(), "周报")

        answer = self.qa.answer(text)
        if answer:
            return BotReply(answer, "问答")
        return BotReply("这个问题我暂时没有把握。已建议转人工处理，或请换个关键词用「搜索 关键词」查资料。", "未知")

    @staticmethod
    def _strip_prefix(text: str, prefixes: tuple[str, ...]) -> str:
        for prefix in prefixes:
            if text.startswith(prefix):
                return text[len(prefix) :].strip(" ：:")
        return text.strip()

    @staticmethod
    def _command_name(text: str) -> str:
        if not text:
            return "帮助"
        return text.split(maxsplit=1)[0].strip("：:")

    @staticmethod
    def _log_interaction(message: IncomingMessage, command: str) -> None:
        with db_connection() as conn:
            conn.execute(
                """
                INSERT INTO interaction_logs(user_id, chat_id, command, raw_text)
                VALUES (?, ?, ?, ?)
                """,
                (message.user_id, message.chat_id, command, message.text),
            )
