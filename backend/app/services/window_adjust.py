"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class WindowAdjustService(BaseModuleService):
    MODULE = "window_adjust"
    ENTITY = "调整记录"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["调整编号", "漏斗编号", "原窗口期", "新窗口期", "影响批次", "调整时间"]
    REQUIRED_FIELDS = ["调整编号", "漏斗编号", "原窗口期"]
    STATUS_ORDER = ["草拟中", "待评审", "已生效", "已回退"]
    ACTION_RULES = {"提交评审": "待评审", "生效调整": "已生效", "回退调整": "已回退"}
    NEGATIVE_ACTIONS = []

    def get_adjusts_for_funnel(self, funnel_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("漏斗编号") == funnel_id]

    def active_window_for_funnel(self, funnel_id: str) -> str:
        adjusts = self.get_adjusts_for_funnel(funnel_id)
        active = next((a for a in adjusts if a.get("status") == "已生效"), None)
        if active:
            return active.get("新窗口期", "")
        return ""

    def parse_affected_batches(self, adjust_id: str) -> list[str]:
        for r in store.rows(self.MODULE):
            if r.get("调整编号") == adjust_id:
                batch_str = r.get("影响批次", "")
                return [b.strip() for b in batch_str.split(",") if b.strip()]
        return []

    def count_pending_adjusts(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") == "待评审")
