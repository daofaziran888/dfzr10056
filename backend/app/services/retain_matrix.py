"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class RetainMatrixService(BaseModuleService):
    MODULE = "retain_matrix"
    ENTITY = "矩阵条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["矩阵编号", "分群编号", "矩阵维度", "观察天数", "版本标记", "生成时间"]
    REQUIRED_FIELDS = ["矩阵编号", "分群编号", "矩阵维度"]
    STATUS_ORDER = ["生成中", "待发布", "已发布", "已作废"]
    ACTION_RULES = {"提交发布": "待发布", "确认发布": "已发布", "作废矩阵": "已作废"}
    NEGATIVE_ACTIONS = ["作废矩阵"]
