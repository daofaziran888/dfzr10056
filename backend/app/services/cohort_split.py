"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CohortSplitService(BaseModuleService):
    MODULE = "cohort_split"
    ENTITY = "分群条目"
    OPERATION_TERM = "切分"
    LIST_FIELDS = ["分群编号", "切分维度", "切分取值", "用户数量", "切分时间", "生效标记"]
    REQUIRED_FIELDS = ["分群编号", "切分维度", "切分取值"]
    STATUS_ORDER = ["切分中", "待生效", "已生效", "已失效"]
    ACTION_RULES = {"提交生效": "待生效", "生效分群": "已生效", "失效分群": "已失效"}
    NEGATIVE_ACTIONS = []
