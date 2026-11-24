"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SegmentRuleService(BaseModuleService):
    MODULE = "segment_rule"
    ENTITY = "规则条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "规则名称", "圈选条件", "覆盖人数", "规则版本", "生效时间"]
    REQUIRED_FIELDS = ["规则编号", "规则名称", "圈选条件"]
    STATUS_ORDER = ["草稿", "待生效", "已生效", "已停用"]
    ACTION_RULES = {"提交生效": "待生效", "启用规则": "已生效", "停用规则": "已停用"}
    NEGATIVE_ACTIONS = ["停用规则"]
