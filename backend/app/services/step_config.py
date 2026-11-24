"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class StepConfigService(BaseModuleService):
    MODULE = "step_config"
    ENTITY = "配置条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["配置编号", "漏斗编号", "步骤序号", "步骤事件", "过滤条件", "更新时间"]
    REQUIRED_FIELDS = ["配置编号", "漏斗编号", "步骤序号"]
    STATUS_ORDER = ["草拟中", "待验证", "已生效", "已废弃"]
    ACTION_RULES = {"提交验证": "待验证", "生效配置": "已生效", "废弃配置": "已废弃"}
    NEGATIVE_ACTIONS = []
