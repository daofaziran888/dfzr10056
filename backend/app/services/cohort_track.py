"""分群追踪·按观察周期计算留存率序列并校验追踪中断，产出追踪明细数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class CohortTrackService(BaseModuleService):
    MODULE = "cohort_track"
    ENTITY = "追踪明细"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["追踪编号", "分群编号", "观察周期", "留存人数", "留存率", "追踪时间"]
    REQUIRED_FIELDS = ["追踪编号", "分群编号", "观察周期"]
    STATUS_ORDER = ["追踪中", "待复核", "已确认", "追踪中断"]
    ACTION_RULES = {"提交复核": "待复核", "确认追踪": "已确认", "登记中断": "追踪中断"}
    NEGATIVE_ACTIONS = []

    def get_tracks_by_cohort(self, cohort_id: str) -> list[dict[str, Any]]:
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("分群编号") == cohort_id]

    def compute_retention_sequence(self, cohort_id: str) -> list[float]:
        tracks = sorted(self.get_tracks_by_cohort(cohort_id),
                        key=lambda t: int(t.get("观察周期", "D0")[1:]))
        return [float(t.get("留存率", 0)) for t in tracks]

    def average_retention(self, cohort_id: str) -> float:
        seq = self.compute_retention_sequence(cohort_id)
        return round(sum(seq) / len(seq), 1) if seq else 0.0

    def latest_retention_rate(self, cohort_id: str) -> float:
        tracks = sorted(self.get_tracks_by_cohort(cohort_id),
                        key=lambda t: int(t.get("观察周期", "D0")[1:]), reverse=True)
        return float(tracks[0].get("留存率", 0)) if tracks else 0.0
