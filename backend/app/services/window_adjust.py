"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class WindowAdjustService(BaseModuleService):
    MODULE = "window_adjust"
    ENTITY = "调整记录"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["调整编号", "漏斗编号", "原窗口期", "新窗口期", "影响批次", "调整时间"]
    REQUIRED_FIELDS = ["调整编号", "漏斗编号", "原窗口期"]
    STATUS_ORDER = ["草拟中", "待评审", "已生效", "已回退"]
    ACTION_RULES = {"提交评审": "待评审", "生效调整": "已生效", "回退调整": "已回退"}
    NEGATIVE_ACTIONS = []
