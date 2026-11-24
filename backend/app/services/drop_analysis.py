"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class DropAnalysisService(BaseModuleService):
    MODULE = "drop_analysis"
    ENTITY = "分析条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["分析编号", "计算编号", "流失步骤", "流失人数", "流失占比", "分析时间"]
    REQUIRED_FIELDS = ["分析编号", "计算编号", "流失步骤"]
    STATUS_ORDER = ["分析中", "待复核", "已复核", "结论存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "结论存疑"}
    NEGATIVE_ACTIONS = []

    def get_by_calc(self, calc_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("计算编号") == calc_id]

    def find_high_drop_steps(self, calc_id: str, threshold: float = 40.0) -> list[dict[str, Any]]:
        analyses = self.get_by_calc(calc_id)
        return [a for a in analyses if float(a.get("流失占比", 0)) >= threshold]

    def total_drop_users(self, calc_id: str) -> int:
        analyses = self.get_by_calc(calc_id)
        return sum(int(a.get("流失人数", 0)) for a in analyses)

    def compare_drop_between_calcs(self, calc_a: str, calc_b: str) -> dict[str, Any]:
        total_a = self.total_drop_users(calc_a)
        total_b = self.total_drop_users(calc_b)
        return {"calc_a": calc_a, "drop_a": total_a, "calc_b": calc_b, "drop_b": total_b, "gap": total_b - total_a}
