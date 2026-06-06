from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request

from app.config import settings
from app.database import init_db
from app.feishu.client import FeishuClient, FeishuClientError
from app.feishu.events import is_url_verification, parse_incoming_message, verify_token
from app.modules.command_router import CommandRouter
from app.modules.bitable_sync import BitableSyncService
from app.modules.push_service import PushService
from app.modules.report_service import ReportService
from app.modules.task_completion_service import TaskCompletionService
from app.modules.task_reminder_service import TaskReminderService
from app.scheduler import create_scheduler


scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
router = CommandRouter()
feishu_client = FeishuClient()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.post("/feishu/events")
async def feishu_events(request: Request) -> dict[str, Any]:
    payload = await request.json()
    if is_url_verification(payload):
        if not verify_token(payload):
            raise HTTPException(status_code=403, detail="Invalid verification token")
        return {"challenge": payload.get("challenge")}

    if not verify_token(payload):
        raise HTTPException(status_code=403, detail="Invalid verification token")

    message = parse_incoming_message(payload)
    if message is None:
        return {"ok": True, "ignored": True}

    if _is_complete_task_command(message.text):
        router._log_interaction(message, "完成任务")
        query = CommandRouter._strip_prefix(message.text.strip(), ("完成任务", "任务完成", "完成"))
        reply_text = await TaskCompletionService(feishu_client=feishu_client).complete_task(message.user_id, query)
        command = "完成任务"
    elif _is_sync_command(message.text):
        router._log_interaction(message, "同步数据")
        if not _is_admin_user(message.user_id):
            reply_text = "你没有权限执行同步数据。"
        else:
            result = await BitableSyncService(feishu_client=feishu_client).sync_all()
            reply_text = f"同步完成：学习资料 {result.materials} 条，个人任务 {result.tasks} 条。"
        command = "同步数据"
    else:
        reply = router.handle(message)
        reply_text = reply.text
        command = reply.command
    if message.chat_id and settings.is_feishu_configured:
        try:
            await feishu_client.send_text(message.chat_id, reply_text)
        except FeishuClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, "command": command, "reply": reply_text}


@app.post("/admin/push/weekly")
async def push_weekly(token: str = Query(...)) -> dict[str, str]:
    _ensure_admin(token)
    text = await PushService(feishu_client=feishu_client).push_weekly_materials()
    return {"status": "sent", "text": text}


@app.get("/admin/report")
async def admin_report(token: str = Query(...)) -> dict[str, str]:
    _ensure_admin(token)
    return {"report": ReportService().weekly_report()}


@app.post("/admin/sync/bitable")
async def sync_bitable(token: str = Query(...)) -> dict[str, int]:
    _ensure_admin(token)
    result = await BitableSyncService(feishu_client=feishu_client).sync_all()
    return {"materials": result.materials, "tasks": result.tasks}


@app.post("/admin/remind/tasks")
async def remind_tasks(token: str = Query(...), days: int = Query(3, ge=0, le=30)) -> dict[str, int]:
    _ensure_admin(token)
    return await TaskReminderService(feishu_client=feishu_client).remind_due_tasks(days)


def _ensure_admin(token: str) -> None:
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")


def _is_complete_task_command(text: str) -> bool:
    return text.strip().startswith(("完成任务", "任务完成", "完成"))


def _is_sync_command(text: str) -> bool:
    return text.strip() in {"同步数据", "同步表格", "刷新数据", "更新数据"}


def _is_admin_user(user_id: str) -> bool:
    return bool(user_id and user_id in settings.admin_user_ids)
