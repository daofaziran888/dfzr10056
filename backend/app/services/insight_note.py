"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class InsightNoteService(BaseModuleService):
    MODULE = "insight_note"
    ENTITY = "笔记条目"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["笔记编号", "分析编号", "洞察摘要", "记录人", "记录时间", "共享标记"]
    REQUIRED_FIELDS = ["笔记编号", "分析编号", "洞察摘要"]
    STATUS_ORDER = ["草拟中", "待共享", "已共享", "已归档"]
    ACTION_RULES = {"提交共享": "待共享", "确认共享": "已共享", "归档笔记": "已归档"}
    NEGATIVE_ACTIONS = []
