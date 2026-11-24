"""分群规则·维护圈选条件并按事件明细计算覆盖人数，产出规则条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class SegmentRuleService(BaseModuleService):
    MODULE = "segment_rule"
    ENTITY = "规则条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "规则名称", "圈选条件", "覆盖人数", "规则版本", "生效时间"]
    REQUIRED_FIELDS = ["规则编号", "规则名称", "圈选条件"]
    STATUS_ORDER = ["草稿", "待生效", "已生效", "已停用"]
    ACTION_RULES = {"提交生效": "待生效", "启用规则": "已生效", "停用规则": "已停用"}
    NEGATIVE_ACTIONS = ["停用规则"]

    def get_active_rules(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") == "已生效"]

    def total_covered_users(self) -> int:
        return sum(int(r.get("覆盖人数", 0)) for r in self.get_active_rules())

    def find_rules_by_condition_keyword(self, keyword: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if keyword in str(r.get("圈选条件", ""))]

    def check_rule_overlap(self, rule_a: str, rule_b: str) -> dict[str, Any]:
        rows = store.rows(self.MODULE)
        a = next((r for r in rows if r.get("规则编号") == rule_a), None)
        b = next((r for r in rows if r.get("规则编号") == rule_b), None)
        if not a or not b:
            return {"overlap_possible": False, "reason": "规则不存在"}
        return {
            "overlap_possible": True,
            "a_users": int(a.get("覆盖人数", 0)),
            "b_users": int(b.get("覆盖人数", 0)),
            "max_overlap": min(int(a.get("覆盖人数", 0)), int(b.get("覆盖人数", 0))),
        }
