"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CaliberCompareService(BaseModuleService):
    MODULE = "caliber_compare"
    ENTITY = "对比记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["对比编号", "漏斗编号", "旧口径转化率", "新口径转化率", "对比差值", "对比时间"]
    REQUIRED_FIELDS = ["对比编号", "漏斗编号", "旧口径转化率"]
    STATUS_ORDER = ["对比中", "待裁决", "已裁决", "对比作废"]
    ACTION_RULES = {"提交裁决": "待裁决", "确认裁决": "已裁决", "作废对比": "对比作废"}
    NEGATIVE_ACTIONS = ["作废对比"]
