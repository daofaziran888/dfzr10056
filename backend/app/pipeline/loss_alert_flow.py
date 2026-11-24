"""流失率→流失预警：监控分群流失率偏离阈值→生成预警条目→按级别处置。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class ChurnAlertResult:
    alert_id: str
    cohort_id: str
    threshold: float
    current_rate: float
    deviation: float
    level: str
    triggered: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "cohort_id": self.cohort_id,
            "threshold": self.threshold,
            "current_rate": self.current_rate,
            "deviation": self.deviation,
            "level": self.level,
            "triggered": self.triggered,
        }


class LossAlertFlow:
    """流失率→流失预警贯通链路：计算分群流失率→与阈值对比→触发预警输出。"""

    HIGH_ALERT_MULTIPLIER = 1.5  # 流失率超阈值 1.5 倍为高级别
    MEDIUM_ALERT_MULTIPLIER = 1.2  # 流失率超阈值 1.2 倍为中级别

    def __init__(self) -> None:
        self._alerts: dict[str, ChurnAlertResult] = {}
        self._counter = 0

    def calculate_churn_rate(self, cohort_id: str) -> float:
        """计算分群当前流失率：1 - 最新观察周期留存率。"""
        tracks = store.rows("cohort_track")
        cohort_tracks = sorted(
            [t for t in tracks if t.get("分群编号") == cohort_id and t.get("status") != "追踪中断"],
            key=lambda t: int(t.get("观察周期", "D0")[1:]),
            reverse=True,
        )
        if not cohort_tracks:
            return 0.0
        latest_retention = float(cohort_tracks[0].get("留存率", 0))
        return round(100 - latest_retention, 1)

    def check_threshold_deviation(
        self, cohort_id: str, threshold: float,
    ) -> ChurnAlertResult:
        """检查流失率是否偏离阈值。"""
        self._counter += 1
        current = self.calculate_churn_rate(cohort_id)
        deviation = round(current - threshold, 1)

        if deviation > 0 and current >= threshold * self.HIGH_ALERT_MULTIPLIER:
            level = "高"
            triggered = True
        elif deviation > 0 and current >= threshold * self.MEDIUM_ALERT_MULTIPLIER:
            level = "中"
            triggered = True
        elif deviation > 0:
            level = "低"
            triggered = True
        else:
            level = "低"
            triggered = False

        result = ChurnAlertResult(
            alert_id=f"CHRN-{self._counter:04d}",
            cohort_id=cohort_id,
            threshold=threshold,
            current_rate=current,
            deviation=deviation,
            level=level,
            triggered=triggered,
        )
        self._alerts[result.alert_id] = result

        if triggered:
            # 写入预警表
            alert_rows = store.rows("churn_alert")
            alert_rows.append({
                "id": max((int(r.get("id", 0)) for r in alert_rows), default=0) + 1,
                "status": "已触发",
                "pending": level != "低",
                "abnormal": level == "高",
                "预警编号": result.alert_id,
                "分群编号": cohort_id,
                "流失阈值": threshold,
                "当前流失率": current,
                "预警级别": level,
                "预警时间": "2026-10-06T10:00",
            })
        return result

    def high_level_alerts(self) -> list[dict[str, Any]]:
        """获取所有高级别预警。"""
        alert_rows = store.rows("churn_alert")
        return [a for a in alert_rows if a.get("预警级别") == "高"]

    def dispose_alert(self, alert_id: str) -> tuple[bool, str]:
        """处置预警：将已触发预警标记为已处置。"""
        alert_rows = store.rows("churn_alert")
        alert = next((a for a in alert_rows if a.get("预警编号") == alert_id), None)
        if alert is None:
            return False, f"预警 {alert_id} 不存在"
        if alert.get("status") != "已触发":
            return False, f"预警 {alert_id} 状态为 {alert.get('status')}"
        alert["status"] = "已处置"
        alert["pending"] = False
        alert["abnormal"] = False
        return True, f"预警 {alert_id} 已处置"

    def release_alert(self, alert_id: str) -> tuple[bool, str]:
        """解除预警：流失率回落后解除。"""
        alert_rows = store.rows("churn_alert")
        alert = next((a for a in alert_rows if a.get("预警编号") == alert_id), None)
        if alert is None:
            return False, f"预警 {alert_id} 不存在"
        alert["status"] = "已解除"
        alert["pending"] = False
        alert["abnormal"] = False
        return True, f"预警 {alert_id} 已解除"

    def snapshot(self) -> dict[str, Any]:
        return {
            "alerts": [a.to_dict() for a in self._alerts.values()],
            "high_count": len(self.high_level_alerts()),
        }