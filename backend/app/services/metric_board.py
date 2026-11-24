"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class MetricBoardService(BaseModuleService):
    MODULE = "metric_board"
    ENTITY = "看板快照"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["快照编号", "统计日期", "漏斗数量", "平均转化率", "活跃分群数", "快照时间"]
    REQUIRED_FIELDS = ["快照编号", "统计日期", "漏斗数量"]
    STATUS_ORDER = ["已生成", "待复核", "已复核", "已发布"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "发布快照": "已发布"}
    NEGATIVE_ACTIONS = []

    def get_snapshots_by_date(self, date: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("统计日期") == date]

    def avg_conversion_trend(self) -> list[float]:
        rows = sorted(store.rows(self.MODULE), key=lambda r: r.get("统计日期", ""))
        return [float(r.get("平均转化率", 0)) for r in rows]

    def latest_snapshot(self) -> dict[str, Any] | None:
        rows = sorted(store.rows(self.MODULE), key=lambda r: r.get("快照时间", ""), reverse=True)
        return rows[0] if rows else None

    def compare_snapshots(self, snap_a: str, snap_b: str) -> dict[str, Any]:
        rows = store.rows(self.MODULE)
        a = next((r for r in rows if r.get("快照编号") == snap_a), {})
        b = next((r for r in rows if r.get("快照编号") == snap_b), {})
        return {
            "conv_rate_diff": round(float(a.get("平均转化率", 0)) - float(b.get("平均转化率", 0)), 1),
            "funnel_count_diff": int(a.get("漏斗数量", 0)) - int(b.get("漏斗数量", 0)),
            "cohort_count_diff": int(a.get("活跃分群数", 0)) - int(b.get("活跃分群数", 0)),
        }
