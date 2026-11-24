"""步骤配置·校验漏斗每步的事件匹配与步骤序号先后判定，产出配置条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class StepConfigService(BaseModuleService):
    MODULE = "step_config"
    ENTITY = "配置条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["配置编号", "漏斗编号", "步骤序号", "步骤事件", "过滤条件", "更新时间"]
    REQUIRED_FIELDS = ["配置编号", "漏斗编号", "步骤序号"]
    STATUS_ORDER = ["草拟中", "待验证", "已生效", "已废弃"]
    ACTION_RULES = {"提交验证": "待验证", "生效配置": "已生效", "废弃配置": "已废弃"}
    NEGATIVE_ACTIONS = []

    def get_steps_for_funnel(self, funnel_id: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        steps = [r for r in rows if r.get("漏斗编号") == funnel_id and r.get("status") == "已生效"]
        steps.sort(key=lambda s: int(s.get("步骤序号", 0)))
        return steps

    def validate_step_order(self, funnel_id: str) -> tuple[bool, str]:
        steps = self.get_steps_for_funnel(funnel_id)
        if not steps:
            return False, "无已生效步骤"
        seqs = [int(s["步骤序号"]) for s in steps]
        expected = list(range(1, len(seqs) + 1))
        if seqs != expected:
            return False, f"步骤序号不连续: {seqs}"
        return True, "步骤序号有序"

    def get_latest_step(self, funnel_id: str) -> dict[str, Any] | None:
        steps = self.get_steps_for_funnel(funnel_id)
        return steps[-1] if steps else None

    def has_duplicate_events(self, funnel_id: str) -> bool:
        steps = self.get_steps_for_funnel(funnel_id)
        events = [s.get("步骤事件", "") for s in steps]
        return len(events) != len(set(events))
