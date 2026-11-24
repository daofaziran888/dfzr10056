"""分群切分→分群追踪：读取已生效分群→生成追踪明细→更新留存数据。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class CohortTrackEntry:
    track_id: str
    cohort_id: str
    period: str
    retained_count: int
    retention_rate: float
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "cohort_id": self.cohort_id,
            "period": self.period,
            "retained_count": self.retained_count,
            "retention_rate": self.retention_rate,
            "status": self.status,
        }


class CohortSplitTrackFlow:
    """分群切分→分群追踪贯通链路：对已生效分群生成多周期追踪明细。"""

    OBSERVE_PERIODS = ["D1", "D3", "D7", "D14", "D30", "D60", "D90", "D180"]

    def __init__(self) -> None:
        self._entries: dict[str, CohortTrackEntry] = {}
        self._counter = 0

    def active_cohorts(self) -> list[dict[str, Any]]:
        """获取所有已生效的分群。"""
        cohorts = store.rows("cohort_split")
        return [c for c in cohorts if c.get("status") == "已生效" and c.get("生效标记") != "已失效"]

    def generate_tracking(self, cohort_id: str) -> list[CohortTrackEntry]:
        """为指定分群生成多观察周期追踪明细。"""
        cohorts = store.rows("cohort_split")
        cohort = next((c for c in cohorts if c.get("分群编号") == cohort_id), None)
        if cohort is None:
            return []
        user_count = int(cohort.get("用户数量", 0))
        if user_count == 0:
            return []

        entries: list[CohortTrackEntry] = []
        previous_count = user_count
        for period in self.OBSERVE_PERIODS:
            days = int(period[1:])
            # 模拟留存衰减：D1 约 90% 留存，后续每天衰减约 1.5%
            retention = max(0, round(previous_count * max(0.1, 1.0 - 0.015 * (days / 2)), 0))
            retention = int(retention)
            rate = round(retention / user_count * 100, 1)
            self._counter += 1
            entry = CohortTrackEntry(
                track_id=f"CTRK-{self._counter:04d}",
                cohort_id=cohort_id,
                period=period,
                retained_count=retention,
                retention_rate=rate,
                status="已确认" if retention > 0 else "追踪中断",
            )
            entries.append(entry)
            self._entries[entry.track_id] = entry

            # 写入追踪明细表
            track_rows = store.rows("cohort_track")
            track_rows.append({
                "id": max((int(r.get("id", 0)) for r in track_rows), default=0) + 1,
                "status": entry.status,
                "pending": entry.status != "已确认",
                "abnormal": entry.status == "追踪中断",
                "追踪编号": entry.track_id,
                "分群编号": cohort_id,
                "观察周期": period,
                "留存人数": retention,
                "留存率": rate,
                "追踪时间": f"2026-10-{(self._counter % 30)+1:02d}T02:00",
            })

        return entries

    def retention_sequence(self, cohort_id: str) -> list[float]:
        """获取分群的留存率序列。"""
        tracks = store.rows("cohort_track")
        cohort_tracks = sorted(
            [t for t in tracks if t.get("分群编号") == cohort_id],
            key=lambda t: int(t.get("观察周期", "D0")[1:]),
        )
        return [float(t.get("留存率", 0)) for t in cohort_tracks]

    def average_retention_rate(self, cohort_id: str) -> float:
        """计算分群在已观察周期内的平均留存率。"""
        seq = self.retention_sequence(cohort_id)
        if not seq:
            return 0.0
        return round(sum(seq) / len(seq), 1)

    def compare_cohort_retention(self, a_id: str, b_id: str) -> dict[str, Any]:
        """比较两个分群的留存表现差异。"""
        rate_a = self.average_retention_rate(a_id)
        rate_b = self.average_retention_rate(b_id)
        return {
            "cohort_a": a_id,
            "retention_a": rate_a,
            "cohort_b": b_id,
            "retention_b": rate_b,
            "gap": round(rate_a - rate_b, 1),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self._entries.values()],
        }