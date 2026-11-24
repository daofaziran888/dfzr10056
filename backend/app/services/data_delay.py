"""延迟登记·登记事件批次到达延迟并校验是否触发补算，产出延迟记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class DataDelayService(BaseModuleService):
    MODULE = "data_delay"
    ENTITY = "延迟记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["延迟编号", "批次编号", "预计到达", "实际到达", "延迟时长", "登记时间"]
    REQUIRED_FIELDS = ["延迟编号", "批次编号", "预计到达"]
    STATUS_ORDER = ["已登记", "评估中", "已补算", "可忽略"]
    ACTION_RULES = {"发起评估": "评估中", "确认补算": "已补算", "标记忽略": "可忽略"}
    NEGATIVE_ACTIONS = []

    def get_delays_for_batch(self, batch_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("批次编号") == batch_id]

    def count_needing_recalc(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") == "评估中" or r.get("status") == "已补算")

    def find_overdue_delays(self, max_hours: float = 24.0) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        overdue = []
        for r in rows:
            delay_str = r.get("延迟时长", "")
            try:
                hours = float("".join(c for c in delay_str if c.isdigit() or c == "."))
            except ValueError:
                hours = 0
            if hours >= max_hours:
                overdue.append(r)
        return overdue
