from __future__ import annotations

import json
from typing import Any

from app.database import db_connection, row_to_dict


def _score_material(row: dict[str, Any], query: str) -> int:
    q = query.lower().strip()
    if not q:
        return 0
    haystack = " ".join(
        [
            row.get("title", ""),
            row.get("category", ""),
            row.get("summary", ""),
            " ".join(row.get("keywords", [])),
        ]
    ).lower()
    score = 0
    if q in row.get("title", "").lower():
        score += 5
    if q in haystack:
        score += 3
    for token in q.split():
        if token and token in haystack:
            score += 1
    return score


class MaterialService:
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        with db_connection() as conn:
            rows = [row_to_dict(row) for row in conn.execute("SELECT * FROM materials ORDER BY id DESC")]
        scored = [(row, _score_material(row, query)) for row in rows]
        return [row for row, score in sorted(scored, key=lambda item: item[1], reverse=True) if score > 0][:limit]

    def weekly_materials(self, limit: int = 5) -> list[dict[str, Any]]:
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM materials
                WHERE is_weekly = 1
                ORDER BY published_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [row_to_dict(row) for row in rows]

    def add_material(
        self,
        title: str,
        category: str,
        keywords: list[str],
        summary: str,
        url: str,
        published_at: str = "",
        is_weekly: bool = False,
    ) -> int:
        with db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO materials(title, category, keywords, summary, url, published_at, is_weekly)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (title, category, json.dumps(keywords, ensure_ascii=False), summary, url, published_at, int(is_weekly)),
            )
            return int(cursor.lastrowid)


def format_materials(materials: list[dict[str, Any]]) -> str:
    if not materials:
        return "没有找到相关学习资料。可以换个关键词试试，例如：团课、青年大学习、主题教育。"
    lines = ["找到以下学习资料："]
    for idx, item in enumerate(materials, start=1):
        url = item.get("url") or "暂无链接"
        summary = item.get("summary") or "暂无摘要"
        lines.append(f"{idx}. {item['title']}\n   摘要：{summary}\n   链接：{url}")
    return "\n".join(lines)

