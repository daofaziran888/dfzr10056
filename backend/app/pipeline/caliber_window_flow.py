"""口径对比→窗口调整：新旧口径转化率差异→触发窗口期重评估→标记影响批次。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class CaliberDiffResult:
    compare_id: str
    funnel_id: str
    old_rate: float
    new_rate: float
    diff: float
    diff_explanation: str
    needs_window_adjust: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "compare_id": self.compare_id,
            "funnel_id": self.funnel_id,
            "old_rate": self.old_rate,
            "new_rate": self.new_rate,
            "diff": self.diff,
            "diff_explanation": self.diff_explanation,
            "needs_window_adjust": self.needs_window_adjust,
        }


class CaliberWindowFlow:
    """口径对比→窗口调整贯通链路：口径切换导致转化率差异→评估是否需窗口期调整→标记受影响批次。"""

    DIFF_SIGNIFICANCE_THRESHOLD = 1.5  # 差异超过 1.5 个百分点为显著差异

    def __init__(self) -> None:
        pass

    def compare_caliber(self, funnel_id: str) -> CaliberDiffResult | None:
        """对比同一漏斗的口径版本差异。"""
        compares = store.rows("caliber_compare")
        records = [c for c in compares if c.get("漏斗编号") == funnel_id]
        if not records:
            return None
        # 取最新对比记录
        latest = max(records, key=lambda c: c.get("对比时间", ""))
        old_rate = float(latest.get("旧口径转化率", 0))
        new_rate = float(latest.get("新口径转化率", 0))
        diff = round(new_rate - old_rate, 1)

        if abs(diff) >= self.DIFF_SIGNIFICANCE_THRESHOLD:
            if diff > 0:
                explanation = f"新口径转化率 {new_rate}% 高于旧口径 {old_rate}%，差值为 {diff} 个百分点，口径变量变更导致测量扩宽"
            else:
                explanation = f"新口径转化率 {new_rate}% 低于旧口径 {old_rate}%，差值为 {abs(diff)} 个百分点，口径收窄排除了部分事件"
            needs_adjust = True
        else:
            explanation = f"新旧口径转化率差额 {abs(diff)} 个百分点，未超过显著阈值 {self.DIFF_SIGNIFICANCE_THRESHOLD} 个百分点"
            needs_adjust = False

        return CaliberDiffResult(
            compare_id=latest.get("对比编号", ""),
            funnel_id=funnel_id,
            old_rate=old_rate,
            new_rate=new_rate,
            diff=diff,
            diff_explanation=explanation,
            needs_window_adjust=needs_adjust,
        )

    def affected_calc_batches(self, funnel_id: str) -> list[dict[str, Any]]:
        """列出受窗口调整影响的历史计算批次。"""
        calcs = store.rows("conv_calc")
        return [c for c in calcs if c.get("漏斗编号") == funnel_id]

    def propose_window_adjust(
        self, funnel_id: str, old_window: str, new_window: str,
    ) -> tuple[bool, str]:
        """提议窗口期调整并记录影响批次。"""
        affected = self.affected_calc_batches(funnel_id)
        affected_ids = ",".join(c.get("计算编号", "") for c in affected)
        adjusts = store.rows("window_adjust")
        adjust_id = f"WADJ-{len(adjusts)+1:03d}"
        adjusts.append({
            "id": max((int(r.get("id", 0)) for r in adjusts), default=0) + 1,
            "status": "待评审",
            "pending": True,
            "abnormal": False,
            "调整编号": adjust_id,
            "漏斗编号": funnel_id,
            "原窗口期": old_window,
            "新窗口期": new_window,
            "影响批次": affected_ids,
            "调整时间": "2026-10-06T16:00",
        })
        return True, f"窗口调整提案 {adjust_id} 已生成，影响 {len(affected)} 个计算批次"

    def history_recalc_decision(self, compare_id: str, decision: str) -> tuple[bool, str]:
        """对口径对比做出是否历史重算的裁决。"""
        compares = store.rows("caliber_compare")
        record = next((c for c in compares if c.get("对比编号") == compare_id), None)
        if record is None:
            return False, f"对比记录 {compare_id} 不存在"
        record["status"] = "已裁决" if decision == "accept" else "对比作废"
        record["pending"] = False
        return True, f"对比 {compare_id} 已裁决：{decision}"

    def snapshot(self) -> dict[str, Any]:
        compares = store.rows("caliber_compare")
        return {
            "compare_count": len(compares),
            "pending_count": sum(1 for c in compares if c.get("status") == "待裁决"),
        }