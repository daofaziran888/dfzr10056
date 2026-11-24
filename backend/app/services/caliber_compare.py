"""口径对比·对比口径版本切换前后的转化率并校验差值裁决，产出对比记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class CaliberCompareService(BaseModuleService):
    MODULE = "caliber_compare"
    ENTITY = "对比记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["对比编号", "漏斗编号", "旧口径转化率", "新口径转化率", "对比差值", "对比时间"]
    REQUIRED_FIELDS = ["对比编号", "漏斗编号", "旧口径转化率"]
    STATUS_ORDER = ["对比中", "待裁决", "已裁决", "对比作废"]
    ACTION_RULES = {"提交裁决": "待裁决", "确认裁决": "已裁决", "作废对比": "对比作废"}
    NEGATIVE_ACTIONS = ["作废对比"]

    def compare_by_funnel(self, funnel_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("漏斗编号") == funnel_id]

    def interpret_diff(self, compare_id: str) -> str:
        for r in store.rows(self.MODULE):
            if r.get("对比编号") == compare_id:
                diff = float(r.get("对比差值", 0))
                if diff >= 2.0:
                    return f"口径切换导致转化率差值 {diff} 个百分点，差异显著，建议历史重算"
                elif diff >= 1.0:
                    return f"口径切换导致转化率差值 {diff} 个百分点，差异较大，需评估影响范围"
                return f"口径切换导致转化率差值 {diff} 个百分点，在可接受范围"
        return "对比记录不存在"

    def find_pending_comparisons(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") == "待裁决"]

    def sign_and_resolve(self, compare_id: str, accept_new: bool) -> tuple[bool, str]:
        for r in store.rows(self.MODULE):
            if r.get("对比编号") == compare_id:
                r["status"] = "已裁决" if accept_new else "对比作废"
                r["pending"] = False
                action = "采纳新口径" if accept_new else "驳回新口径"
                return True, f"对比 {compare_id} 裁决完成：{action}"
        return False, "对比记录不存在"
