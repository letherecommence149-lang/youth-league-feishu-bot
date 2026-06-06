from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.config import settings


class FeishuClientError(RuntimeError):
    pass


class FeishuClient:
    base_url = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: str | None = None, app_secret: str | None = None) -> None:
        self.app_id = app_id or settings.feishu_app_id
        self.app_secret = app_secret or settings.feishu_app_secret
        self._tenant_access_token = ""
        self._token_expires_at = 0.0

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.request(method, path, **kwargs)
            try:
                payload = response.json()
            except ValueError:
                response.raise_for_status()
                raise FeishuClientError(f"Feishu API returned non-JSON response: {response.text}")
            if response.status_code >= 400:
                raise FeishuClientError(f"Feishu API HTTP {response.status_code}: {payload}")
        if payload.get("code", 0) != 0:
            raise FeishuClientError(f"Feishu API error: {payload}")
        return payload

    async def tenant_access_token(self) -> str:
        now = time.time()
        if self._tenant_access_token and now < self._token_expires_at - 60:
            return self._tenant_access_token
        if not self.app_id or not self.app_secret:
            raise FeishuClientError("FEISHU_APP_ID and FEISHU_APP_SECRET are required.")
        payload = await self._request(
            "POST",
            "/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        self._tenant_access_token = payload["tenant_access_token"]
        self._token_expires_at = now + int(payload.get("expire", 7200))
        return self._tenant_access_token

    async def send_text(self, receive_id: str, text: str, receive_id_type: str = "chat_id") -> dict[str, Any]:
        token = await self.tenant_access_token()
        return await self._request(
            "POST",
            f"/im/v1/messages?receive_id_type={receive_id_type}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False),
            },
        )

    async def send_post(
        self,
        receive_id: str,
        title: str,
        lines: list[str],
        receive_id_type: str = "chat_id",
    ) -> dict[str, Any]:
        token = await self.tenant_access_token()
        content = {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": line}] for line in lines],
                }
            }
        }
        return await self._request(
            "POST",
            f"/im/v1/messages?receive_id_type={receive_id_type}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": receive_id,
                "msg_type": "post",
                "content": json.dumps(content, ensure_ascii=False),
            },
        )

    async def search_bitable_records(
        self,
        app_token: str,
        table_id: str,
        field_names: list[str] | None = None,
        page_size: int = 500,
    ) -> list[dict[str, Any]]:
        token = await self.tenant_access_token()
        records: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params: dict[str, Any] = {
                "page_size": page_size,
                "text_field_as_array": "true",
                "user_id_type": "open_id",
            }
            if page_token:
                params["page_token"] = page_token
            body: dict[str, Any] = {}
            if field_names:
                body["field_names"] = field_names
            payload = await self._request(
                "POST",
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=body,
            )
            data = payload.get("data", {})
            records.extend(data.get("items", []))
            if not data.get("has_more"):
                return records
            page_token = data.get("page_token", "")
            if not page_token:
                return records

    async def get_wiki_node(self, wiki_token: str) -> dict[str, Any]:
        token = await self.tenant_access_token()
        payload = await self._request(
            "GET",
            "/wiki/v2/spaces/get_node",
            headers={"Authorization": f"Bearer {token}"},
            params={"token": wiki_token},
        )
        return payload.get("data", {}).get("node", {})

    async def update_bitable_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        token = await self.tenant_access_token()
        return await self._request(
            "PUT",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"fields": fields},
        )
