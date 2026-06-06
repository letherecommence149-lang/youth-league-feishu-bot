from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.database import db_connection, init_db
from app.feishu.client import FeishuClient


MATERIAL_FIELD_NAMES = ["标题", "分类", "关键词", "摘要", "链接", "发布时间", "发布日期", "是否本周推荐"]
TASK_FIELD_NAMES = ["用户ID", "用户id", "任务标题", "标题", "状态", "截止时间", "截止日期"]


@dataclass(frozen=True)
class SyncResult:
    materials: int = 0
    tasks: int = 0


class BitableSyncService:
    def __init__(self, feishu_client: FeishuClient | None = None) -> None:
        self.feishu = feishu_client or FeishuClient()
        self._resolved_app_token = ""

    async def sync_all(self) -> SyncResult:
        init_db()
        material_count = 0
        task_count = 0
        if settings.feishu_bitable_materials_table_id:
            material_count = await self.sync_materials()
        if settings.feishu_bitable_tasks_table_id:
            task_count = await self.sync_tasks()
        return SyncResult(materials=material_count, tasks=task_count)

    async def sync_materials(self) -> int:
        records = await self.feishu.search_bitable_records(
            await self._app_token(),
            settings.feishu_bitable_materials_table_id,
        )
        count = 0
        for record in records:
            fields = record.get("fields", {})
            title = _field_text(fields, "标题")
            if not title:
                continue
            _upsert_material(
                external_id=record.get("record_id", ""),
                title=title,
                category=_field_text(fields, "分类") or "学习材料",
                keywords=_field_keywords(fields, "关键词"),
                summary=_field_text(fields, "摘要"),
                url=_field_url(fields, "链接"),
                published_at=_first_date(fields, "发布时间", "发布日期"),
                is_weekly=_field_bool(fields, "是否本周推荐"),
            )
            count += 1
        return count

    async def sync_tasks(self) -> int:
        records = await self.feishu.search_bitable_records(
            await self._app_token(),
            settings.feishu_bitable_tasks_table_id,
        )
        count = 0
        for record in records:
            fields = record.get("fields", {})
            user_id = _first_text(fields, "用户ID", "用户id")
            title = _field_text(fields, "任务标题") or _field_text(fields, "标题")
            if not user_id or not title:
                continue
            _upsert_task(
                external_id=record.get("record_id", ""),
                user_id=user_id,
                title=title,
                status=_field_text(fields, "状态") or "待完成",
                due_at=_field_date(fields, "截止时间") or _field_date(fields, "截止日期"),
            )
            count += 1
        return count

    async def _app_token(self) -> str:
        if self._resolved_app_token:
            return self._resolved_app_token
        if settings.feishu_bitable_app_token:
            self._resolved_app_token = settings.feishu_bitable_app_token
            return self._resolved_app_token
        node = await self.feishu.get_wiki_node(settings.feishu_bitable_wiki_token)
        self._resolved_app_token = str(node.get("obj_token") or "")
        if not self._resolved_app_token:
            raise RuntimeError("Unable to resolve bitable app_token from FEISHU_BITABLE_WIKI_TOKEN.")
        return self._resolved_app_token


def _upsert_material(
    external_id: str,
    title: str,
    category: str,
    keywords: list[str],
    summary: str,
    url: str,
    published_at: str,
    is_weekly: bool,
) -> None:
    source = "feishu_bitable:materials"
    with db_connection() as conn:
        row = conn.execute(
            "SELECT id FROM materials WHERE external_source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        values = (
            title,
            category,
            json.dumps(keywords, ensure_ascii=False),
            summary,
            url,
            published_at,
            int(is_weekly),
            source,
            external_id,
        )
        if row:
            conn.execute(
                """
                UPDATE materials
                SET title = ?, category = ?, keywords = ?, summary = ?, url = ?,
                    published_at = ?, is_weekly = ?, synced_at = CURRENT_TIMESTAMP
                WHERE external_source = ? AND external_id = ?
                """,
                values,
            )
        else:
            conn.execute(
                """
                INSERT INTO materials(
                    title, category, keywords, summary, url, published_at, is_weekly,
                    external_source, external_id, synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                values,
            )


def _upsert_task(external_id: str, user_id: str, title: str, status: str, due_at: str) -> None:
    source = "feishu_bitable:tasks"
    with db_connection() as conn:
        row = conn.execute(
            "SELECT id FROM tasks WHERE external_source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        values = (user_id, title, status, due_at, source, external_id)
        if row:
            conn.execute(
                """
                UPDATE tasks
                SET user_id = ?, title = ?, status = ?, due_at = ?,
                    updated_at = CURRENT_TIMESTAMP, synced_at = CURRENT_TIMESTAMP
                WHERE external_source = ? AND external_id = ?
                """,
                values,
            )
        else:
            conn.execute(
                """
                INSERT INTO tasks(user_id, title, status, due_at, external_source, external_id, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                values,
            )


def _field_text(fields: dict[str, Any], name: str) -> str:
    return _plain_text(fields.get(name)).strip()


def _first_text(fields: dict[str, Any], *names: str) -> str:
    for name in names:
        text = _field_text(fields, name)
        if text:
            return text
    return ""


def _field_url(fields: dict[str, Any], name: str) -> str:
    value = fields.get(name)
    if isinstance(value, dict):
        return str(value.get("link") or value.get("url") or value.get("text") or "").strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and (item.get("link") or item.get("url")):
                return str(item.get("link") or item.get("url")).strip()
    return _plain_text(value).strip()


def _field_keywords(fields: dict[str, Any], name: str) -> list[str]:
    value = fields.get(name)
    if isinstance(value, list):
        items = [_plain_text(item).strip() for item in value]
    else:
        items = re.split(r"[,，、\n]+", _plain_text(value))
    return [item for item in (part.strip() for part in items) if item]


def _field_bool(fields: dict[str, Any], name: str) -> bool:
    value = fields.get(name)
    if isinstance(value, bool):
        return value
    text = _plain_text(value).strip().lower()
    return text in {"1", "true", "yes", "y", "是", "本周", "推荐"}


def _field_date(fields: dict[str, Any], name: str) -> str:
    value = fields.get(name)
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    return _plain_text(value).strip()


def _first_date(fields: dict[str, Any], *names: str) -> str:
    for name in names:
        date = _field_date(fields, name)
        if date:
            return date
    return ""


def _plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_plain_text(item) for item in value if _plain_text(item))
    if isinstance(value, dict):
        for key in ("text", "name", "link", "url", "value"):
            if key in value:
                return _plain_text(value[key])
        return json.dumps(value, ensure_ascii=False)
    return str(value)
