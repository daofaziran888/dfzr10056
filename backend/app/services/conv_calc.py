"""转化计算·按日计算漏斗转化并对进入与转化人数做去重用户统计，产出计算批次数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ConvCalcService(BaseModuleService):
    MODULE = "conv_calc"
    ENTITY = "计算批次"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["计算编号", "漏斗编号", "统计日期", "进入人数", "转化人数", "计算耗时", "生成时间"]
    REQUIRED_FIELDS = ["计算编号", "漏斗编号", "统计日期"]
    STATUS_ORDER = ["计算中", "待复核", "已确认", "计算失败"]
    ACTION_RULES = {"提交复核": "待复核", "确认结果": "已确认", "登记失败": "计算失败"}
    NEGATIVE_ACTIONS = []

    def get_calc_by_funnel(self, funnel_id: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("漏斗编号") == funnel_id]

    def compute_conversion_rate(self, calc_id: str) -> float:
        rows = store.rows(self.MODULE)
        calc = next((r for r in rows if r.get("计算编号") == calc_id), None)
        if calc is None:
            return 0.0
        entry = int(calc.get("进入人数", 0))
        conv = int(calc.get("转化人数", 0))
        return round(conv / entry * 100, 1) if entry > 0 else 0.0

    def find_failed_calcs(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") == "计算失败"]

    def total_conv_users(self, funnel_id: str) -> int:
        rows = store.rows(self.MODULE)
        return sum(int(r.get("转化人数", 0)) for r in rows
                   if r.get("漏斗编号") == funnel_id and r.get("status") == "已确认")

    def compare_calc_conv(self, calc_a: str, calc_b: str) -> dict[str, Any]:
        rows = store.rows(self.MODULE)
        a = next((r for r in rows if r.get("计算编号") == calc_a), {})
        b = next((r for r in rows if r.get("计算编号") == calc_b), {})
        return {
            "a_rate": self.compute_conversion_rate(calc_a),
            "b_rate": self.compute_conversion_rate(calc_b),
            "diff": abs(int(a.get("转化人数", 0)) - int(b.get("转化人数", 0))),
        }
