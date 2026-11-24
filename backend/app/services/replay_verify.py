"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReplayVerifyService(BaseModuleService):
    MODULE = "replay_verify"
    ENTITY = "校验记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["校验编号", "计算编号", "原转化人数", "重放转化人数", "差异条数", "校验时间"]
    REQUIRED_FIELDS = ["校验编号", "计算编号", "原转化人数"]
    STATUS_ORDER = ["重放中", "待校验", "校验通过", "差异待判"]
    ACTION_RULES = {"提交校验": "待校验", "通过校验": "校验通过", "登记待判": "差异待判"}
    NEGATIVE_ACTIONS = []
