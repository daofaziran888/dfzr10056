"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DataDelayService(BaseModuleService):
    MODULE = "data_delay"
    ENTITY = "延迟记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["延迟编号", "批次编号", "预计到达", "实际到达", "延迟时长", "登记时间"]
    REQUIRED_FIELDS = ["延迟编号", "批次编号", "预计到达"]
    STATUS_ORDER = ["已登记", "评估中", "已补算", "可忽略"]
    ACTION_RULES = {"发起评估": "评估中", "确认补算": "已补算", "标记忽略": "可忽略"}
    NEGATIVE_ACTIONS = []
