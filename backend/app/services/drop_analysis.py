"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DropAnalysisService(BaseModuleService):
    MODULE = "drop_analysis"
    ENTITY = "分析条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["分析编号", "计算编号", "流失步骤", "流失人数", "流失占比", "分析时间"]
    REQUIRED_FIELDS = ["分析编号", "计算编号", "流失步骤"]
    STATUS_ORDER = ["分析中", "待复核", "已复核", "结论存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "结论存疑"}
    NEGATIVE_ACTIONS = []
