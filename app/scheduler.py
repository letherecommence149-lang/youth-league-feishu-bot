from __future__ import annotations

import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.modules.bitable_sync import BitableSyncService
from app.modules.push_service import PushService
from app.modules.task_reminder_service import TaskReminderService


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    if settings.weekly_push_enabled:
        scheduler.add_job(
            lambda: asyncio.run(PushService().push_weekly_materials()),
            "cron",
            day_of_week=settings.weekly_push_day_of_week,
            hour=settings.weekly_push_hour,
            minute=settings.weekly_push_minute,
            id="weekly_material_push",
            replace_existing=True,
        )
    if settings.task_reminder_enabled:
        scheduler.add_job(
            lambda: asyncio.run(TaskReminderService().remind_due_tasks()),
            "cron",
            hour=settings.task_reminder_hour,
            minute=settings.task_reminder_minute,
            id="task_reminder",
            replace_existing=True,
        )
    if settings.bitable_auto_sync_enabled and settings.is_bitable_configured:
        scheduler.add_job(
            lambda: asyncio.run(BitableSyncService().sync_all()),
            "interval",
            minutes=settings.bitable_auto_sync_interval_minutes,
            id="bitable_auto_sync",
            replace_existing=True,
        )
    return scheduler
