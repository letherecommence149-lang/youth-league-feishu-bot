from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _list_env(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "智慧团建一键学Bot")
    app_env: str = os.getenv("APP_ENV", "development")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "./data/bot.sqlite3"))
    admin_token: str = os.getenv("ADMIN_TOKEN", "change-me")
    admin_user_ids: tuple[str, ...] = _list_env("ADMIN_USER_IDS")

    feishu_app_id: str = os.getenv("FEISHU_APP_ID", "")
    feishu_app_secret: str = os.getenv("FEISHU_APP_SECRET", "")
    feishu_verification_token: str = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
    feishu_encrypt_key: str = os.getenv("FEISHU_ENCRYPT_KEY", "")
    feishu_default_chat_id: str = os.getenv("FEISHU_DEFAULT_CHAT_ID", "")

    feishu_bitable_app_token: str = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
    feishu_bitable_wiki_token: str = os.getenv("FEISHU_BITABLE_WIKI_TOKEN", "")
    feishu_bitable_materials_table_id: str = os.getenv("FEISHU_BITABLE_MATERIALS_TABLE_ID", "")
    feishu_bitable_tasks_table_id: str = os.getenv("FEISHU_BITABLE_TASKS_TABLE_ID", "")

    weekly_push_enabled: bool = _bool_env("WEEKLY_PUSH_ENABLED", False)
    weekly_push_day_of_week: str = os.getenv("WEEKLY_PUSH_CRON_DAY_OF_WEEK", "mon")
    weekly_push_hour: int = _int_env("WEEKLY_PUSH_CRON_HOUR", 8)
    weekly_push_minute: int = _int_env("WEEKLY_PUSH_CRON_MINUTE", 30)

    task_reminder_enabled: bool = _bool_env("TASK_REMINDER_ENABLED", False)
    task_reminder_hour: int = _int_env("TASK_REMINDER_CRON_HOUR", 9)
    task_reminder_minute: int = _int_env("TASK_REMINDER_CRON_MINUTE", 0)
    task_reminder_lookahead_days: int = _int_env("TASK_REMINDER_LOOKAHEAD_DAYS", 3)

    bitable_auto_sync_enabled: bool = _bool_env("BITABLE_AUTO_SYNC_ENABLED", False)
    bitable_auto_sync_interval_minutes: int = _int_env("BITABLE_AUTO_SYNC_INTERVAL_MINUTES", 10)

    @property
    def is_feishu_configured(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret)

    @property
    def is_bitable_configured(self) -> bool:
        return bool(self.feishu_bitable_app_token or self.feishu_bitable_wiki_token)


settings = Settings()
