"""漏斗定义·维护步骤序列与转化窗口期并校验口径版本，产出漏斗条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class FunnelDefService(BaseModuleService):
    MODULE = "funnel_def"
    ENTITY = "漏斗条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["漏斗编号", "漏斗名称", "步骤数", "窗口期", "口径版本", "创建时间"]
    REQUIRED_FIELDS = ["漏斗编号", "漏斗名称", "步骤数"]
    STATUS_ORDER = ["草稿", "待评审", "已发布", "已下线"]
    ACTION_RULES = {"提交评审": "待评审", "发布漏斗": "已发布", "下线漏斗": "已下线"}
    NEGATIVE_ACTIONS = ["下线漏斗"]

    def get_by_funnel_id(self, funnel_id: str) -> dict[str, Any] | None:
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("漏斗编号") == funnel_id:
                return r
        return None

    def count_published(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") == "已发布")

    def validate_step_count(self, funnel_id: str, declared: int) -> bool:
        funnel = self.get_by_funnel_id(funnel_id)
        if funnel is None:
            return False
        return int(funnel.get("步骤数", 0)) == declared

    def get_caliber_version(self, funnel_id: str) -> str:
        funnel = self.get_by_funnel_id(funnel_id)
        return funnel.get("口径版本", "") if funnel else ""
