"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ChurnAlertService(BaseModuleService):
    MODULE = "churn_alert"
    ENTITY = "预警条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["预警编号", "分群编号", "流失阈值", "当前流失率", "预警级别", "预警时间"]
    REQUIRED_FIELDS = ["预警编号", "分群编号", "流失阈值"]
    STATUS_ORDER = ["已触发", "确认中", "已处置", "已解除"]
    ACTION_RULES = {"提交确认": "确认中", "处置预警": "已处置", "解除预警": "已解除"}
    NEGATIVE_ACTIONS = []
