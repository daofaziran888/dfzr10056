"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class RetainMatrixService(BaseModuleService):
    MODULE = "retain_matrix"
    ENTITY = "矩阵条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["矩阵编号", "分群编号", "矩阵维度", "观察天数", "版本标记", "生成时间"]
    REQUIRED_FIELDS = ["矩阵编号", "分群编号", "矩阵维度"]
    STATUS_ORDER = ["生成中", "待发布", "已发布", "已作废"]
    ACTION_RULES = {"提交发布": "待发布", "确认发布": "已发布", "作废矩阵": "已作废"}
    NEGATIVE_ACTIONS = ["作废矩阵"]

    def get_by_cohort(self, cohort_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("分群编号") == cohort_id]

    def get_latest_version(self, cohort_id: str) -> dict[str, Any] | None:
        matrices = sorted(
            self.get_by_cohort(cohort_id),
            key=lambda m: m.get("生成时间", ""),
            reverse=True,
        )
        return matrices[0] if matrices else None

    def mark_version_tag(self, matrix_id: str, tag: str) -> tuple[bool, str]:
        for r in store.rows(self.MODULE):
            if r.get("矩阵编号") == matrix_id:
                r["版本标记"] = tag
                return True, f"矩阵 {matrix_id} 版本标记更新为 {tag}"
        return False, "矩阵不存在"

    def get_version_mismatches(self, expected_tag: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE)
                if r.get("版本标记") != expected_tag and r.get("status") == "已发布"]
