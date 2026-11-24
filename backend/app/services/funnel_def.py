"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FunnelDefService(BaseModuleService):
    MODULE = "funnel_def"
    ENTITY = "漏斗条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["漏斗编号", "漏斗名称", "步骤数", "窗口期", "口径版本", "创建时间"]
    REQUIRED_FIELDS = ["漏斗编号", "漏斗名称", "步骤数"]
    STATUS_ORDER = ["草稿", "待评审", "已发布", "已下线"]
    ACTION_RULES = {"提交评审": "待评审", "发布漏斗": "已发布", "下线漏斗": "已下线"}
    NEGATIVE_ACTIONS = ["下线漏斗"]
