from __future__ import annotations

from app.config import settings
from app.feishu.client import FeishuClient
from app.modules.material_service import MaterialService, format_materials


class PushService:
    def __init__(self, feishu_client: FeishuClient | None = None, material_service: MaterialService | None = None) -> None:
        self.feishu = feishu_client or FeishuClient()
        self.materials = material_service or MaterialService()

    async def push_weekly_materials(self, chat_id: str | None = None) -> str:
        target_chat_id = chat_id or settings.feishu_default_chat_id
        if not target_chat_id:
            raise ValueError("FEISHU_DEFAULT_CHAT_ID is required for weekly push.")
        text = "本周学习材料已更新：\n" + format_materials(self.materials.weekly_materials())
        await self.feishu.send_text(target_chat_id, text)
        return text

