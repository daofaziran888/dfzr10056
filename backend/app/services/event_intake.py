"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class EventIntakeService(BaseModuleService):
    MODULE = "event_intake"
    ENTITY = "接入批次"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["批次编号", "事件来源", "窗口起点", "窗口终点", "事件条数", "接入时间"]
    REQUIRED_FIELDS = ["批次编号", "事件来源", "窗口起点"]
    STATUS_ORDER = ["接入中", "待校验", "已就绪", "接入失败"]
    ACTION_RULES = {"提交校验": "待校验", "确认就绪": "已就绪", "登记失败": "接入失败"}
    NEGATIVE_ACTIONS = []

    def find_by_batch_id(self, batch_id: str) -> dict[str, Any] | None:
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("批次编号") == batch_id:
                return r
        return None

    def count_batches_by_source(self, source: str) -> int:
        rows = store.rows(self.MODULE)
        return sum(1 for r in rows if r.get("事件来源") == source)

    def get_batches_in_window(self, start: str, end: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if start <= str(r.get("窗口起点", "")) and str(r.get("窗口终点", "")) <= end]

    def count_events_ready(self) -> int:
        rows = store.rows(self.MODULE)
        return sum(int(r.get("事件条数", 0)) for r in rows if r.get("status") == "已就绪")
