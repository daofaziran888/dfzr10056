"""分群追踪→留存矩阵：读取分群追踪数据→构建留存矩阵→版本标记。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class RetentionMatrix:
    matrix_id: str
    cohort_id: str
    dimensions: str
    observe_days: str
    version_tag: str
    retention_series: list[float]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "cohort_id": self.cohort_id,
            "dimensions": self.dimensions,
            "observe_days": self.observe_days,
            "version_tag": self.version_tag,
            "series_length": len(self.retention_series),
        }


class TrackMatrixFlow:
    """分群追踪→留存矩阵贯通链路：收集分群追踪数据，构建分群×观察期的留存矩阵。"""

    def __init__(self) -> None:
        self._matrices: dict[str, RetentionMatrix] = {}
        self._counter = 0

    def build_matrix(
        self, cohort_id: str, version_tag: str = "v1.0-口径",
    ) -> RetentionMatrix | None:
        """从追踪明细构建留存矩阵。"""
        tracks = store.rows("cohort_track")
        cohort_tracks = sorted(
            [t for t in tracks if t.get("分群编号") == cohort_id and t.get("status") != "追踪中断"],
            key=lambda t: int(t.get("观察周期", "D0")[1:]),
        )
        if not cohort_tracks:
            return None

        observe_days = ",".join(t.get("观察周期", "") for t in cohort_tracks)
        retention_series = [float(t.get("留存率", 0)) for t in cohort_tracks]
        dim_count = len(cohort_tracks)
        self._counter += 1

        matrix = RetentionMatrix(
            matrix_id=f"RMTX-{self._counter:04d}",
            cohort_id=cohort_id,
            dimensions=f"{dim_count}观察周期×1分群",
            observe_days=observe_days,
            version_tag=version_tag,
            retention_series=retention_series,
            generated_at=f"2026-10-{self._counter+2:02d}T06:00",
        )
        self._matrices[matrix.matrix_id] = matrix

        # 写入矩阵表
        mat_rows = store.rows("retain_matrix")
        mat_rows.append({
            "id": max((int(r.get("id", 0)) for r in mat_rows), default=0) + 1,
            "status": "已发布",
            "pending": False,
            "abnormal": False,
            "矩阵编号": matrix.matrix_id,
            "分群编号": cohort_id,
            "矩阵维度": matrix.dimensions,
            "观察天数": observe_days,
            "版本标记": version_tag,
            "生成时间": matrix.generated_at,
        })
        return matrix

    def mark_version(self, matrix_id: str, new_tag: str) -> tuple[bool, str]:
        """更新矩阵版本标记：口径切换后重新标记。"""
        mat_rows = store.rows("retain_matrix")
        matrix = next((m for m in mat_rows if m.get("矩阵编号") == matrix_id), None)
        if matrix is None:
            return False, f"矩阵 {matrix_id} 不存在"
        old_tag = matrix.get("版本标记", "")
        matrix["版本标记"] = new_tag
        if new_tag != old_tag:
            matrix["status"] = "待发布"
            matrix["pending"] = True
        return True, f"版本标记从 '{old_tag}' 更新为 '{new_tag}'"

    def get_version_mismatch_matrices(self, target_tag: str) -> list[dict[str, Any]]:
        """返回版本标记不匹配当前口径的矩阵列表。"""
        mat_rows = store.rows("retain_matrix")
        return [m for m in mat_rows if m.get("版本标记") != target_tag and m.get("status") == "已发布"]

    def publish_matrix(self, matrix_id: str) -> tuple[bool, str]:
        """发布待发布状态的留存矩阵。"""
        mat_rows = store.rows("retain_matrix")
        matrix = next((m for m in mat_rows if m.get("矩阵编号") == matrix_id), None)
        if matrix is None:
            return False, f"矩阵 {matrix_id} 不存在"
        if matrix.get("status") != "待发布":
            return False, f"矩阵 {matrix_id} 状态为 {matrix.get('status')}"
        matrix["status"] = "已发布"
        matrix["pending"] = False
        return True, f"矩阵 {matrix_id} 已发布"

    def snapshot(self) -> dict[str, Any]:
        return {
            "matrices": [m.to_dict() for m in self._matrices.values()],
        }