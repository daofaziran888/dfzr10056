"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EventIntakeService(BaseModuleService):
    MODULE = "event_intake"
    ENTITY = "接入批次"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["批次编号", "事件来源", "窗口起点", "窗口终点", "事件条数", "接入时间"]
    REQUIRED_FIELDS = ["批次编号", "事件来源", "窗口起点"]
    STATUS_ORDER = ["接入中", "待校验", "已就绪", "接入失败"]
    ACTION_RULES = {"提交校验": "待校验", "确认就绪": "已就绪", "登记失败": "接入失败"}
    NEGATIVE_ACTIONS = []
