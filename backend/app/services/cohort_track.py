"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CohortTrackService(BaseModuleService):
    MODULE = "cohort_track"
    ENTITY = "追踪明细"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["追踪编号", "分群编号", "观察周期", "留存人数", "留存率", "追踪时间"]
    REQUIRED_FIELDS = ["追踪编号", "分群编号", "观察周期"]
    STATUS_ORDER = ["追踪中", "待复核", "已确认", "追踪中断"]
    ACTION_RULES = {"提交复核": "待复核", "确认追踪": "已确认", "登记中断": "追踪中断"}
    NEGATIVE_ACTIONS = []
