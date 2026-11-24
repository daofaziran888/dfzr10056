"""事件接入→去重：统计批次重复条数→标记去重→更新批次就绪状态。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class DedupResult:
    batch_id: str
    dedup_id: str
    total_events: int
    duplicate_count: int
    retained_count: int
    dedup_rule: str
    status: str = "去重中"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dedup_id": self.dedup_id,
            "batch_id": self.batch_id,
            "total_events": self.total_events,
            "duplicate_count": self.duplicate_count,
            "retained_count": self.retained_count,
            "dedup_rule": self.dedup_rule,
            "status": self.status,
        }


class IntakeDedupFlow:
    """事件接入→去重贯通链路。"""

    DUPLICATE_ALERT_THRESHOLD = 5000

    def __init__(self) -> None:
        self._results: dict[str, DedupResult] = {}
        self._counter = 0

    def run_dedup(self, batch_id: str, rule: str = "user_id+event_name+ts_minute") -> DedupResult:
        """对已接入批次执行去重：查询事件条数、计算重复、生成去重记录。"""
        batches = store.rows("event_intake")
        batch = next((r for r in batches if r.get("批次编号") == batch_id), None)
        if batch is None:
            raise ValueError(f"批次 {batch_id} 不存在")
        total = int(batch.get("事件条数", 0))
        self._counter += 1

        # 查询已有去重记录
        dedup_rows = store.rows("event_dedup")
        existing = next((r for r in dedup_rows if r.get("批次编号") == batch_id), None)
        dup_count = int(existing.get("重复条数", 0)) if existing else 0
        retained = total - dup_count

        result = DedupResult(
            batch_id=batch_id,
            dedup_id=f"EDDP-{self._counter:04d}",
            total_events=total,
            duplicate_count=dup_count,
            retained_count=retained,
            dedup_rule=rule,
            status="已确认" if dup_count < self.DUPLICATE_ALERT_THRESHOLD else "待复核",
        )
        if existing:
            existing["status"] = result.status
            existing["重复条数"] = dup_count
            existing["保留条数"] = retained
            existing["去重规则"] = rule
            existing["去重时间"] = "2026-10-06T00:00"
        else:
            dedup_rows.append({
                "id": max((int(r.get("id", 0)) for r in dedup_rows), default=0) + 1,
                "status": result.status,
                "pending": result.status != "已确认",
                "abnormal": dup_count >= self.DUPLICATE_ALERT_THRESHOLD,
                "去重编号": result.dedup_id,
                "批次编号": batch_id,
                "重复条数": dup_count,
                "去重规则": rule,
                "保留条数": retained,
                "去重时间": "2026-10-06T00:00",
            })
        self._results[result.dedup_id] = result
        return result

    def unique_user_count(self, batch_id: str) -> int:
        """基于去重后保留条数估算去重用户数。"""
        dedup_rows = store.rows("event_dedup")
        record = next((r for r in dedup_rows if r.get("批次编号") == batch_id), None)
        if record is None:
            return 0
        retained = int(record.get("保留条数", 0))
        # 按平均每用户 1.8 条事件估算
        return max(1, int(retained / 1.8))

    def duplicate_alert_batches(self) -> list[dict[str, Any]]:
        """返回重复条数超阈值的批次列表。"""
        dedup_rows = store.rows("event_dedup")
        return [r for r in dedup_rows if int(r.get("重复条数", 0)) >= self.DUPLICATE_ALERT_THRESHOLD]

    def is_batch_ready_for_funnel(self, batch_id: str) -> bool:
        """判定批次是否已去重且可进入漏斗计算。"""
        batches = store.rows("event_intake")
        batch = next((r for r in batches if r.get("批次编号") == batch_id), None)
        if batch is None:
            return False
        if batch.get("status") != "已就绪":
            return False
        dedup_rows = store.rows("event_dedup")
        record = next((r for r in dedup_rows if r.get("批次编号") == batch_id), None)
        return record is not None and record.get("status") == "已确认"

    def snapshot(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self._results.values()],
            "duplicate_alert_count": len(self.duplicate_alert_batches()),
        }