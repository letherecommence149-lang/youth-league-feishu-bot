from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.feishu.events import IncomingMessage
from app.modules.command_router import CommandRouter


class FakeMaterials:
    def search(self, query: str):
        return [{"title": "团课材料", "summary": f"query={query}", "url": "https://example.com"}]

    def weekly_materials(self):
        return [{"title": "本周学习", "summary": "推荐阅读", "url": "https://example.com/weekly"}]


class FakeQa:
    def answer(self, question: str):
        if "团课" in question:
            return "团课补学说明"
        return None


class FakeActivities:
    def signup(self, activity_name: str, user_id: str, user_name: str = ""):
        return f"已报名:{activity_name}:{user_id}"


class FakeTasks:
    def list_user_tasks(self, user_id: str):
        return f"任务:{user_id}"


class FakeReports:
    def weekly_report(self):
        return "周报"


def build_router() -> CommandRouter:
    router = CommandRouter(FakeMaterials(), FakeQa(), FakeActivities(), FakeTasks(), FakeReports())
    router._log_interaction = lambda message, command: None
    return router


def message(text: str) -> IncomingMessage:
    return IncomingMessage("im.message.receive_v1", "mid", "cid", "uid", "user", text)


def test_help_command():
    reply = build_router().handle(message("帮助"))
    assert "可用指令" in reply.text
    assert reply.command == "帮助"


def test_search_command():
    reply = build_router().handle(message("搜索 团课"))
    assert "团课材料" in reply.text
    assert "query=团课" in reply.text


def test_activity_signup_command():
    reply = build_router().handle(message("活动报名 春季团课"))
    assert reply.text == "已报名:春季团课:uid"


def test_my_id_command():
    reply = build_router().handle(message("我的ID"))
    assert reply.text == "你的飞书 open_id 是：uid"
    assert reply.command == "我的ID"


def test_faq_fallback():
    reply = build_router().handle(message("团课怎么补"))
    assert reply.text == "团课补学说明"
