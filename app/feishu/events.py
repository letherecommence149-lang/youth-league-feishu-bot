from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.config import settings


@dataclass(frozen=True)
class IncomingMessage:
    event_type: str
    message_id: str
    chat_id: str
    user_id: str
    user_name: str
    text: str


def is_url_verification(payload: dict[str, Any]) -> bool:
    return payload.get("type") == "url_verification"


def verify_token(payload: dict[str, Any]) -> bool:
    expected = settings.feishu_verification_token
    if not expected:
        return True
    token = payload.get("token") or payload.get("header", {}).get("token")
    return token == expected


def parse_event_type(payload: dict[str, Any]) -> str:
    return payload.get("header", {}).get("event_type") or payload.get("type", "")


def _extract_text_content(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, dict):
        text = content.get("text", "")
    else:
        try:
            text = json.loads(content).get("text", "")
        except (json.JSONDecodeError, TypeError):
            text = str(content)
    text = re.sub(r"<at[^>]*>.*?</at>", "", text)
    text = re.sub(r"^@\S+\s*", "", text)
    return text.strip()


def parse_incoming_message(payload: dict[str, Any]) -> IncomingMessage | None:
    event_type = parse_event_type(payload)
    event = payload.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})
    sender_id = sender.get("sender_id", {})

    if not message:
        return None

    user_name = sender.get("sender_type", "")
    return IncomingMessage(
        event_type=event_type,
        message_id=message.get("message_id", ""),
        chat_id=message.get("chat_id", ""),
        user_id=sender_id.get("open_id") or sender_id.get("user_id") or "",
        user_name=user_name,
        text=_extract_text_content(message),
    )
