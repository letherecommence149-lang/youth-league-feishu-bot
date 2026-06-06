from __future__ import annotations

from app.database import db_connection


class ReportService:
    def weekly_report(self) -> str:
        with db_connection() as conn:
            interactions = conn.execute(
                "SELECT COUNT(*) AS count FROM interaction_logs WHERE created_at >= datetime('now', '-7 days')"
            ).fetchone()["count"]
            signups = conn.execute(
                "SELECT COUNT(*) AS count FROM activity_signups WHERE created_at >= datetime('now', '-7 days')"
            ).fetchone()["count"]
            open_tasks = conn.execute("SELECT COUNT(*) AS count FROM tasks WHERE status != '已完成'").fetchone()["count"]
            popular = conn.execute(
                """
                SELECT command, COUNT(*) AS count
                FROM interaction_logs
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY command
                ORDER BY count DESC
                LIMIT 5
                """
            ).fetchall()

        lines = [
            "团支部 Bot 周报",
            f"- 近 7 天交互次数：{interactions}",
            f"- 近 7 天活动报名：{signups}",
            f"- 当前未完成任务：{open_tasks}",
        ]
        if popular:
            lines.append("- 热门指令：" + "、".join(f"{row['command']}({row['count']})" for row in popular))
        return "\n".join(lines)

