"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FunnelVersionService(BaseModuleService):
    MODULE = "funnel_version"
    ENTITY = "版本条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["版本号", "漏斗编号", "变更摘要", "发布人", "发布时间", "版本状态"]
    REQUIRED_FIELDS = ["版本号", "漏斗编号", "变更摘要"]
    STATUS_ORDER = ["草拟中", "待发布", "已发布", "已回滚"]
    ACTION_RULES = {"提交发布": "待发布", "确认发布": "已发布", "回滚版本": "已回滚"}
    NEGATIVE_ACTIONS = ["回滚版本"]
