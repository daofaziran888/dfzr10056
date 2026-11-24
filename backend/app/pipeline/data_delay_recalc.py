"""延迟登记→补算评估：登记批次到达延迟→评估是否超过窗口期→触发补算或标记忽略。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class DelayRecalcResult:
    delay_id: str
    batch_id: str
    expected_arrive: str
    actual_arrive: str
    delay_hours: float
    exceeds_window: bool
    needs_recalc: bool
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay_id": self.delay_id,
            "batch_id": self.batch_id,
            "expected_arrive": self.expected_arrive,
            "actual_arrive": self.actual_arrive,
            "delay_hours": self.delay_hours,
            "exceeds_window": self.exceeds_window,
            "needs_recalc": self.needs_recalc,
            "verdict": self.verdict,
        }


class DataDelayRecalcFlow:
    """延迟登记→补算贯通链路：评估批次延迟对漏斗计算的影响，决策是否发起补算。"""

    DEFAULT_WINDOW_HOURS = 24.0  # 默认窗口期24小时
    SHORT_WINDOW_HOURS = 6.0  # 短窗口期

    def __init__(self) -> None:
        self._results: dict[str, DelayRecalcResult] = {}
        self._counter = 0

    def register_delay(
        self, batch_id: str, expected: str, actual: str,
    ) -> DelayRecalcResult:
        """登记批次延迟并评估是否需要补算。"""
        self._counter += 1
        delay_id = f"DDLY-{self._counter:04d}"

        # 计算延迟时长
        delay_hours = self._calc_delay_hours(expected, actual)

        # 查询漏斗窗口期判定
        exceeds = delay_hours >= self.DEFAULT_WINDOW_HOURS
        needs_recalc = delay_hours >= self.SHORT_WINDOW_HOURS

        if delay_hours < self.SHORT_WINDOW_HOURS:
            verdict = f"延迟 {delay_hours} 小时未超过短窗口期 {self.SHORT_WINDOW_HOURS} 小时，可忽略"
        elif exceeds:
            verdict = f"延迟 {delay_hours} 小时超过默认窗口期 {self.DEFAULT_WINDOW_HOURS} 小时，需补算受影响的计算批次"
        else:
            verdict = f"延迟 {delay_hours} 小时，需评估对窗口内计算的影响后决定是否补算"

        result = DelayRecalcResult(
            delay_id=delay_id,
            batch_id=batch_id,
            expected_arrive=expected,
            actual_arrive=actual,
            delay_hours=delay_hours,
            exceeds_window=exceeds,
            needs_recalc=needs_recalc,
            verdict=verdict,
        )
        self._results[delay_id] = result

        # 写入延迟记录
        delay_rows = store.rows("data_delay")
        delay_rows.append({
            "id": max((int(r.get("id", 0)) for r in delay_rows), default=0) + 1,
            "status": "已补算" if needs_recalc else "可忽略",
            "pending": exceeds,
            "abnormal": exceeds,
            "延迟编号": delay_id,
            "批次编号": batch_id,
            "预计到达": expected,
            "实际到达": actual,
            "延迟时长": f"{delay_hours}小时",
            "登记时间": "2026-10-06T10:00",
        })
        return result

    def _calc_delay_hours(self, expected: str, actual: str) -> float:
        """计算延迟小时数（简化实现）。"""
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M"
            t1 = datetime.strptime(expected, fmt)
            t2 = datetime.strptime(actual, fmt)
            return round(abs((t2 - t1).total_seconds()) / 3600, 1)
        except (ValueError, ImportError):
            return 0.0

    def batches_needing_recalc(self) -> list[dict[str, Any]]:
        """获取需要补算的事件接入批次。"""
        delay_rows = store.rows("data_delay")
        return [d for d in delay_rows if d.get("status") == "已补算"]

    def ignore_short_delays(self) -> int:
        """标记短延迟记录为可忽略。"""
        delay_rows = store.rows("data_delay")
        count = 0
        for d in delay_rows:
            delay_str = d.get("延迟时长", "")
            try:
                hours = float("".join(c for c in delay_str if c.isdigit() or c == "."))
            except ValueError:
                hours = 0
            if hours < self.SHORT_WINDOW_HOURS and d.get("status") != "可忽略":
                d["status"] = "可忽略"
                d["pending"] = False
                count += 1
        return count

    def snapshot(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self._results.values()],
            "needs_recalc_count": len(self.batches_needing_recalc()),
        }