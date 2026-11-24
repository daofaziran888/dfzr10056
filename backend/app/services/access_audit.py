"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class AccessAuditService(BaseModuleService):
    MODULE = "access_audit"
    ENTITY = "审计明细"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["审计编号", "访问者", "访问数据集", "访问行数", "访问时间", "用途标记"]
    REQUIRED_FIELDS = ["审计编号", "访问者", "访问数据集"]
    STATUS_ORDER = ["已记录", "待复核", "已复核", "存疑中"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "存疑中"}
    NEGATIVE_ACTIONS = []

    def get_by_visitor(self, visitor: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("访问者") == visitor]

    def get_by_dataset(self, dataset: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("访问数据集") == dataset]

    def count_suspicious_audits(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") == "存疑中")

    def total_rows_accessed(self) -> int:
        return sum(int(r.get("访问行数", 0)) for r in store.rows(self.MODULE))
