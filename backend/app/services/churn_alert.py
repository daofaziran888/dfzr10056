"""流失预警·监控分群流失率相对阈值的偏离并校验预警级别，产出预警条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ChurnAlertService(BaseModuleService):
    MODULE = "churn_alert"
    ENTITY = "预警条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["预警编号", "分群编号", "流失阈值", "当前流失率", "预警级别", "预警时间"]
    REQUIRED_FIELDS = ["预警编号", "分群编号", "流失阈值"]
    STATUS_ORDER = ["已触发", "确认中", "已处置", "已解除"]
    ACTION_RULES = {"提交确认": "确认中", "处置预警": "已处置", "解除预警": "已解除"}
    NEGATIVE_ACTIONS = []

    def check_threshold_deviation(self, cohort_id: str, threshold: float, current_rate: float) -> tuple[bool, str]:
        deviation = current_rate - threshold
        if deviation > 0:
            if current_rate >= threshold * 1.5:
                return True, f"流失率 {current_rate}% 超阈值 {threshold}% 1.5倍，触发高级别预警"
            elif current_rate >= threshold * 1.2:
                return True, f"流失率 {current_rate}% 超阈值 {threshold}% 1.2倍，触发中级别预警"
            return True, f"流失率 {current_rate}% 超过阈值 {threshold}%，触发低级别预警"
        return False, f"流失率 {current_rate}% 未超过阈值 {threshold}%"

    def get_high_level_alerts(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("预警级别") == "高"]

    def dispose_alert(self, alert_id: str) -> tuple[bool, str]:
        for r in store.rows(self.MODULE):
            if r.get("预警编号") == alert_id and r.get("status") == "已触发":
                r["status"] = "已处置"
                r["pending"] = False
                return True, f"预警 {alert_id} 已处置"
        return False, "预警不存在或不可处置"

    def active_alert_count(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") in ("已触发", "确认中"))
