from __future__ import annotations

from app.feishu.events import parse_incoming_message


def test_parse_group_at_message_strips_feishu_at_placeholder():
    payload = {
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_x"}, "sender_type": "user"},
            "message": {
                "message_id": "om_x",
                "chat_id": "oc_x",
                "content": "{\"text\":\"@_user_1 帮助\"}",
            },
        },
    }

    message = parse_incoming_message(payload)

    assert message is not None
    assert message.text == "帮助"
