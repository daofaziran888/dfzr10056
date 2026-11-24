"""重放校验·用相同事件明细重放转化计算并比对差异条数，产出校验记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ReplayVerifyService(BaseModuleService):
    MODULE = "replay_verify"
    ENTITY = "校验记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["校验编号", "计算编号", "原转化人数", "重放转化人数", "差异条数", "校验时间"]
    REQUIRED_FIELDS = ["校验编号", "计算编号", "原转化人数"]
    STATUS_ORDER = ["重放中", "待校验", "校验通过", "差异待判"]
    ACTION_RULES = {"提交校验": "待校验", "通过校验": "校验通过", "登记待判": "差异待判"}
    NEGATIVE_ACTIONS = []

    def compare_diff_count(self, verify_a: str, verify_b: str) -> dict[str, Any]:
        rows = store.rows(self.MODULE)
        a = next((r for r in rows if r.get("校验编号") == verify_a), {})
        b = next((r for r in rows if r.get("校验编号") == verify_b), {})
        return {
            "a_diff": int(a.get("差异条数", 0)),
            "b_diff": int(b.get("差异条数", 0)),
            "gap": int(a.get("差异条数", 0)) - int(b.get("差异条数", 0)),
        }

    def find_diff_verifications(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") == "差异待判"]

    def deterministic_ratio(self) -> float:
        rows = store.rows(self.MODULE)
        total = len(rows)
        passed = sum(1 for r in rows if r.get("status") == "校验通过")
        return round(passed / total * 100, 1) if total > 0 else 0.0

    def get_verification_for_calc(self, calc_id: str) -> dict[str, Any] | None:
        for r in store.rows(self.MODULE):
            if r.get("计算编号") == calc_id:
                return r
        return None
