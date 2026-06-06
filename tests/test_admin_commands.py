from __future__ import annotations

from app.main import _is_admin_user, _is_sync_command
from app.config import settings


def test_sync_command_aliases():
    assert _is_sync_command("同步数据")
    assert _is_sync_command("同步表格")
    assert not _is_sync_command("我的任务")


def test_admin_user_uses_configured_open_id():
    original_admins = settings.admin_user_ids
    object.__setattr__(settings, "admin_user_ids", ("ou_admin",))
    try:
        assert _is_admin_user("ou_admin")
        assert not _is_admin_user("ou_other")
    finally:
        object.__setattr__(settings, "admin_user_ids", original_admins)
