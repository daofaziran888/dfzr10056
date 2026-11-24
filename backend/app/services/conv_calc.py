"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ConvCalcService(BaseModuleService):
    MODULE = "conv_calc"
    ENTITY = "计算批次"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["计算编号", "漏斗编号", "统计日期", "进入人数", "转化人数", "计算耗时", "生成时间"]
    REQUIRED_FIELDS = ["计算编号", "漏斗编号", "统计日期"]
    STATUS_ORDER = ["计算中", "待复核", "已确认", "计算失败"]
    ACTION_RULES = {"提交复核": "待复核", "确认结果": "已确认", "登记失败": "计算失败"}
    NEGATIVE_ACTIONS = []
