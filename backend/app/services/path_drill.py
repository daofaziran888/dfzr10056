"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PathDrillService(BaseModuleService):
    MODULE = "path_drill"
    ENTITY = "下钻条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["下钻编号", "计算编号", "下钻路径", "路径人数", "路径占比", "下钻时间"]
    REQUIRED_FIELDS = ["下钻编号", "计算编号", "下钻路径"]
    STATUS_ORDER = ["下钻中", "待复核", "已复核", "路径存疑"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "登记存疑": "路径存疑"}
    NEGATIVE_ACTIONS = []
