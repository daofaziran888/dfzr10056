"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class CohortSplitService(BaseModuleService):
    MODULE = "cohort_split"
    ENTITY = "分群条目"
    OPERATION_TERM = "切分"
    LIST_FIELDS = ["分群编号", "切分维度", "切分取值", "用户数量", "切分时间", "生效标记"]
    REQUIRED_FIELDS = ["分群编号", "切分维度", "切分取值"]
    STATUS_ORDER = ["切分中", "待生效", "已生效", "已失效"]
    ACTION_RULES = {"提交生效": "待生效", "生效分群": "已生效", "失效分群": "已失效"}
    NEGATIVE_ACTIONS = []

    def get_active_cohorts(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") == "已生效" and r.get("生效标记") != "已失效"]

    def count_users_by_dimension(self, dimension: str) -> int:
        rows = store.rows(self.MODULE)
        return sum(int(r.get("用户数量", 0)) for r in rows if r.get("切分维度") == dimension)

    def find_cohort_by_id(self, cohort_id: str) -> dict[str, Any] | None:
        for r in store.rows(self.MODULE):
            if r.get("分群编号") == cohort_id:
                return r
        return None

    def total_active_users(self) -> int:
        return sum(int(c.get("用户数量", 0)) for c in self.get_active_cohorts())
