"""口径切换→历史重算评估：口径版本变更后评估历史计算批次是否需要重算并生成评估结论。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class RecalcAssessment:
    assessment_id: str
    funnel_id: str
    old_version: str
    new_version: str
    affected_batches: list[str]
    total_batches: int
    recalc_recommended: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "funnel_id": self.funnel_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "affected_batches": self.affected_batches,
            "total_batches": self.total_batches,
            "recalc_recommended": self.recalc_recommended,
            "reason": self.reason,
        }


class CaliberRecalcFlow:
    """口径切换→历史重算评估贯通链路。"""

    RECALC_DIFF_THRESHOLD = 1.0  # 口径差值超过1个百分点建议重算

    def __init__(self) -> None:
        self._assessments: dict[str, RecalcAssessment] = {}
        self._counter = 0

    def get_funnel_versions(self, funnel_id: str) -> list[dict[str, Any]]:
        """获取漏斗的所有版本记录。"""
        versions = store.rows("funnel_version")
        return [v for v in versions if v.get("漏斗编号") == funnel_id]

    def assess_recalc_need(
        self, funnel_id: str, old_ver: str, new_ver: str,
    ) -> RecalcAssessment:
        """评估口径切换后是否需要历史批次重算。"""
        self._counter += 1
        # 查找受影响的计算批次
        calcs = store.rows("conv_calc")
        affected = [c.get("计算编号", "") for c in calcs if c.get("漏斗编号") == funnel_id]

        # 查找口径对比差值
        compares = store.rows("caliber_compare")
        latest_compare = next(
            (c for c in compares if c.get("漏斗编号") == funnel_id and c.get("status") == "待裁决"),
            None,
        )
        diff = float(latest_compare.get("对比差值", 0)) if latest_compare else 0

        recommends = abs(diff) >= self.RECALC_DIFF_THRESHOLD
        if recommends:
            reason = f"口径差值 {diff} 个百分点超过重算阈值 {self.RECALC_DIFF_THRESHOLD}，{len(affected)} 个历史批次需以新口径重算"
        else:
            reason = f"口径差值 {diff} 个百分点未超过重算阈值，历史批次可保持原有计算结果"

        assessment = RecalcAssessment(
            assessment_id=f"RCAS-{self._counter:04d}",
            funnel_id=funnel_id,
            old_version=old_ver,
            new_version=new_ver,
            affected_batches=affected,
            total_batches=len(affected),
            recalc_recommended=recommends,
            reason=reason,
        )
        self._assessments[assessment.assessment_id] = assessment

        # 更新漏斗版本状态
        versions = store.rows("funnel_version")
        for v in versions:
            if v.get("漏斗编号") == funnel_id and v.get("版本号") == old_ver:
                v["版本状态"] = "待重算" if recommends else "生效中"
        return assessment

    def commit_version_rollback(
        self, funnel_id: str, version: str,
    ) -> tuple[bool, str]:
        """回滚漏斗版本：将指定版本标记为已回滚。"""
        versions = store.rows("funnel_version")
        target = next(
            (v for v in versions
             if v.get("漏斗编号") == funnel_id and v.get("版本号") == version),
            None,
        )
        if target is None:
            return False, f"版本 {version} 不存在"
        target["版本状态"] = "已回滚"
        target["status"] = "已回滚"
        target["pending"] = False
        target["abnormal"] = True
        return True, f"漏斗 {funnel_id} 版本 {version} 已回滚"

    def get_affected_step_configs(self, funnel_id: str) -> list[dict[str, Any]]:
        """获取受口径变更影响的步骤配置。"""
        configs = store.rows("step_config")
        return [c for c in configs if c.get("漏斗编号") == funnel_id]

    def snapshot(self) -> dict[str, Any]:
        return {
            "assessments": [a.to_dict() for a in self._assessments.values()],
        }