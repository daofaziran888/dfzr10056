"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class PathDrillService(BaseModuleService):
    MODULE = "path_drill"
    ENTITY = "下钻条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["下钻编号", "计算编号", "下钻路径", "路径人数", "路径占比", "下钻时间"]
    REQUIRED_FIELDS = ["下钻编号", "计算编号", "下钻路径"]
    STATUS_ORDER = ["下钻中", "待复核", "已复核", "路径存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "路径存疑"}
    NEGATIVE_ACTIONS = []

    def get_paths_for_calc(self, calc_id: str) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("计算编号") == calc_id]

    def find_main_path(self, calc_id: str) -> dict[str, Any] | None:
        paths = self.get_paths_for_calc(calc_id)
        return max(paths, key=lambda p: int(p.get("路径人数", 0))) if paths else None

    def total_path_users(self, calc_id: str) -> int:
        paths = self.get_paths_for_calc(calc_id)
        return sum(int(p.get("路径人数", 0)) for p in paths)

    def discover_long_tail_paths(self, calc_id: str, threshold_pct: float = 10.0) -> list[dict[str, Any]]:
        paths = self.get_paths_for_calc(calc_id)
        return [p for p in paths if float(p.get("路径占比", 0)) <= threshold_pct]
