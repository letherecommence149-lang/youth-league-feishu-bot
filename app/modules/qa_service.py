from __future__ import annotations

import json
from typing import Any

from app.database import db_connection, row_to_dict


def _score_faq(row: dict[str, Any], question: str) -> int:
    q = question.lower().strip()
    haystack = " ".join([row.get("question", ""), row.get("answer", ""), " ".join(row.get("keywords", []))]).lower()
    score = 0
    if q and q in row.get("question", "").lower():
        score += 6
    if q and q in haystack:
        score += 3
    for token in q.split():
        if token and token in haystack:
            score += 1
    return score


class QaService:
    def answer(self, question: str) -> str | None:
        with db_connection() as conn:
            rows = [row_to_dict(row) for row in conn.execute("SELECT * FROM faqs ORDER BY id DESC")]
        matches = sorted(((row, _score_faq(row, question)) for row in rows), key=lambda item: item[1], reverse=True)
        if not matches or matches[0][1] <= 0:
            return None
        row = matches[0][0]
        return f"{row['answer']}\n\n来源：团支部 FAQ"

    def add_faq(self, question: str, answer: str, keywords: list[str]) -> int:
        with db_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO faqs(question, answer, keywords) VALUES (?, ?, ?)",
                (question, answer, json.dumps(keywords, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

