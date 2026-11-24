"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class FunnelVersionService(BaseModuleService):
    MODULE = "funnel_version"
    ENTITY = "版本条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["版本号", "漏斗编号", "变更摘要", "发布人", "发布时间", "版本状态"]
    REQUIRED_FIELDS = ["版本号", "漏斗编号", "变更摘要"]
    STATUS_ORDER = ["草拟中", "待发布", "已发布", "已回滚"]
    ACTION_RULES = {"提交发布": "待发布", "确认发布": "已发布", "回滚版本": "已回滚"}
    NEGATIVE_ACTIONS = ["回滚版本"]

    def get_versions_for_funnel(self, funnel_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("漏斗编号") == funnel_id]

    def get_active_version(self, funnel_id: str) -> str:
        versions = self.get_versions_for_funnel(funnel_id)
        active = next((v for v in versions if v.get("版本状态") == "生效中"), None)
        return active.get("版本号", "") if active else ""

    def latest_version_for_funnel(self, funnel_id: str) -> dict[str, Any] | None:
        versions = sorted(
            self.get_versions_for_funnel(funnel_id),
            key=lambda v: v.get("发布时间", ""),
            reverse=True,
        )
        return versions[0] if versions else None

    def find_rolled_back_versions(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("版本状态") == "已回滚"]
