"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ExportTaskService(BaseModuleService):
    MODULE = "export_task"
    ENTITY = "任务单"
    OPERATION_TERM = "导出"
    LIST_FIELDS = ["任务编号", "导出范围", "导出格式", "记录条数", "生成时间"]
    REQUIRED_FIELDS = ["任务编号", "导出范围", "导出格式"]
    STATUS_ORDER = ["排队中", "导出中", "已完成", "导出失败"]
    ACTION_RULES = {"发起导出": "导出中", "确认完成": "已完成", "登记失败": "导出失败"}
    NEGATIVE_ACTIONS = []

    def get_pending_tasks(self) -> list[dict[str, Any]]:
        return [r for r in store.rows(self.MODULE) if r.get("status") in ("排队中", "导出中")]

    def total_records_exported(self) -> int:
        return sum(int(r.get("记录条数", 0)) for r in store.rows(self.MODULE) if r.get("status") == "已完成")

    def count_failed_tasks(self) -> int:
        return sum(1 for r in store.rows(self.MODULE) if r.get("status") == "导出失败")
