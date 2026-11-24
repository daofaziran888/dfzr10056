"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class StepDetailService(BaseModuleService):
    MODULE = "step_detail"
    ENTITY = "明细条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["明细编号", "计算编号", "步骤序号", "进入人数", "转化人数", "转化率", "流失人数"]
    REQUIRED_FIELDS = ["明细编号", "计算编号", "步骤序号"]
    STATUS_ORDER = ["已生成", "待复核", "已复核", "数据存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "数据存疑"}
    NEGATIVE_ACTIONS = []
