"""步骤明细·计算每步进入与流失并复核数据存疑条目，产出明细条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class StepDetailService(BaseModuleService):
    MODULE = "step_detail"
    ENTITY = "明细条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["明细编号", "计算编号", "步骤序号", "进入人数", "转化人数", "转化率", "流失人数"]
    REQUIRED_FIELDS = ["明细编号", "计算编号", "步骤序号"]
    STATUS_ORDER = ["已生成", "待复核", "已复核", "数据存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "数据存疑"}
    NEGATIVE_ACTIONS = []

    def get_details_by_calc(self, calc_id: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("计算编号") == calc_id]

    def compute_overall_drop_rate(self, calc_id: str) -> float:
        details = self.get_details_by_calc(calc_id)
        total_entered = sum(int(d.get("进入人数", 0)) for d in details)
        last_conv = details[-1].get("转化人数", 0) if details else 0
        return round((1 - int(last_conv) / total_entered) * 100, 1) if total_entered > 0 else 0.0

    def find_highest_drop_step(self, calc_id: str) -> dict[str, Any] | None:
        details = self.get_details_by_calc(calc_id)
        if not details:
            return None
        return max(details, key=lambda d: int(d.get("流失人数", 0)))

    def step_conv_rate_descending(self, calc_id: str) -> list[dict[str, Any]]:
        details = self.get_details_by_calc(calc_id)
        return sorted(details, key=lambda d: float(d.get("转化率", 0)), reverse=True)

    def detect_anomalous_drop(self, calc_id: str, threshold_pct: float = 50.0) -> list[dict[str, Any]]:
        details = self.get_details_by_calc(calc_id)
        return [d for d in details if float(d.get("流失占比", float(d.get("流失人数", 0)) / max(float(d.get("进入人数", 1)), 1) * 100)) > threshold_pct]
