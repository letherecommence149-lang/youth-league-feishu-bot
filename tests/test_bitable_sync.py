from __future__ import annotations

from app.modules.bitable_sync import _field_bool, _field_date, _field_keywords, _field_text, _field_url


def test_bitable_field_parsers_handle_common_field_shapes():
    fields = {
        "标题": [{"text": "青年大学习第 1 期"}],
        "关键词": ["青年大学习", "团课"],
        "链接": {"link": "https://example.com/study", "text": "学习链接"},
        "发布时间": 1780531200000,
        "是否本周推荐": True,
    }

    assert _field_text(fields, "标题") == "青年大学习第 1 期"
    assert _field_keywords(fields, "关键词") == ["青年大学习", "团课"]
    assert _field_url(fields, "链接") == "https://example.com/study"
    assert _field_date(fields, "发布时间") == "2026-06-04"
    assert _field_bool(fields, "是否本周推荐") is True


def test_keywords_can_be_split_from_text():
    assert _field_keywords({"关键词": "青年大学习, 团课、主题教育"}, "关键词") == [
        "青年大学习",
        "团课",
        "主题教育",
    ]
