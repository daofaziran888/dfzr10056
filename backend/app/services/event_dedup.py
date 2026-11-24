"""事件去重·按用户与事件指纹对接入事件做去重并计算保留条数，产出去重记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class EventDedupService(BaseModuleService):
    MODULE = "event_dedup"
    ENTITY = "去重记录"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["去重编号", "批次编号", "重复条数", "去重规则", "保留条数", "去重时间"]
    REQUIRED_FIELDS = ["去重编号", "批次编号", "重复条数"]
    STATUS_ORDER = ["去重中", "待复核", "已确认", "规则失效"]
    ACTION_RULES = {"提交复核": "待复核", "确认去重": "已确认", "失效规则": "规则失效"}
    NEGATIVE_ACTIONS = []

    def count_unique_users(self, batch_id: str) -> float:
        rows = store.rows(self.MODULE)
        record = next((r for r in rows if r.get("批次编号") == batch_id), None)
        if record is None:
            return 0.0
        retained = int(record.get("保留条数", 0))
        return retained / 1.8  # 平均每用户 1.8 条事件

    def find_high_duplicate_batches(self, threshold: int = 5000) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if int(r.get("重复条数", 0)) >= threshold]

    def duplicate_ratio(self, batch_id: str) -> float:
        rows = store.rows(self.MODULE)
        record = next((r for r in rows if r.get("批次编号") == batch_id), None)
        if record is None:
            return 0.0
        dup = int(record.get("重复条数", 0))
        retained = int(record.get("保留条数", 0))
        total = dup + retained
        return round(dup / total * 100, 1) if total > 0 else 0.0
