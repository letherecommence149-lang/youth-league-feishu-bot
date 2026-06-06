from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import init_db
from app.modules.material_service import MaterialService
from app.modules.qa_service import QaService


def main() -> None:
    init_db()
    materials = MaterialService()
    qa = QaService()
    materials.add_material(
        title="青年大学习春季专题学习",
        category="青年大学习",
        keywords=["青年大学习", "团课", "春季"],
        summary="本周团员理论学习推荐材料，适合作为团日活动前置阅读。",
        url="https://example.com/youth-study",
        published_at="2026-05-31",
        is_weekly=True,
    )
    materials.add_material(
        title="三会两制一课制度说明",
        category="团务制度",
        keywords=["三会两制一课", "团务", "制度"],
        summary="介绍支部大会、支委会、团小组会、团员教育评议、团员年度注册和团课制度。",
        url="https://example.com/league-rules",
        published_at="2026-05-31",
        is_weekly=True,
    )
    qa.add_faq(
        question="团课怎么补",
        answer="如果错过团课，请先查看群内本周学习材料，完成补学后向组织委员登记。具体补交流程以支部通知为准。",
        keywords=["团课", "补学", "请假"],
    )
    qa.add_faq(
        question="如何报名活动",
        answer="在群里 @Bot 并发送「活动报名 活动名称」即可报名，例如「活动报名 春季团课学习活动」。",
        keywords=["活动", "报名", "团日"],
    )
    print("Demo data seeded.")


if __name__ == "__main__":
    main()

