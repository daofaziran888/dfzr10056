"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EventDedupService(BaseModuleService):
    MODULE = "event_dedup"
    ENTITY = "去重记录"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["去重编号", "批次编号", "重复条数", "去重规则", "保留条数", "去重时间"]
    REQUIRED_FIELDS = ["去重编号", "批次编号", "重复条数"]
    STATUS_ORDER = ["去重中", "待复核", "已确认", "规则失效"]
    ACTION_RULES = {"提交复核": "待复核", "确认去重": "已确认", "失效规则": "规则失效"}
    NEGATIVE_ACTIONS = []
