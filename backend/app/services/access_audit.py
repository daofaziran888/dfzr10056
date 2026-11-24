"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class AccessAuditService(BaseModuleService):
    MODULE = "access_audit"
    ENTITY = "审计明细"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["审计编号", "访问者", "访问数据集", "访问行数", "访问时间", "用途标记"]
    REQUIRED_FIELDS = ["审计编号", "访问者", "访问数据集"]
    STATUS_ORDER = ["已记录", "待复核", "已复核", "存疑中"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "存疑中"}
    NEGATIVE_ACTIONS = []
