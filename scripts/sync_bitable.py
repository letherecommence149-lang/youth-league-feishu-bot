from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.modules.bitable_sync import BitableSyncService


async def main() -> None:
    if not settings.is_bitable_configured:
        raise SystemExit("FEISHU_BITABLE_APP_TOKEN is required.")
    result = await BitableSyncService().sync_all()
    print(f"Synced materials={result.materials}, tasks={result.tasks}")


if __name__ == "__main__":
    asyncio.run(main())
