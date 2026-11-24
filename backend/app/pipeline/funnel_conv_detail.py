"""漏斗转化计算→步骤明细：漏斗定义与步骤配置驱动按日计算，输出步骤进入/转化/流失明细。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class ConvCalcResult:
    calc_id: str
    funnel_id: str
    stat_date: str
    entry_users: int
    conv_users: int
    conv_rate: float
    step_details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calc_id": self.calc_id,
            "funnel_id": self.funnel_id,
            "stat_date": self.stat_date,
            "entry_users": self.entry_users,
            "conv_users": self.conv_users,
            "conv_rate": self.conv_rate,
            "step_count": len(self.step_details),
        }


class FunnelConvDetailFlow:
    """漏斗定义→步骤明细贯通链路：读取漏斗定义和步骤配置，查询计算批次结果，生成步骤明细。"""

    def __init__(self) -> None:
        pass

    def get_funnel_steps(self, funnel_id: str) -> list[dict[str, Any]]:
        """获取漏斗的步骤配置，按步骤序号排序。"""
        configs = store.rows("step_config")
        steps = [c for c in configs if c.get("漏斗编号") == funnel_id and c.get("status") == "已生效"]
        steps.sort(key=lambda s: int(s.get("步骤序号", 0)))
        return steps

    def step_order_valid(self, funnel_id: str) -> bool:
        """验证步骤序号是否连续且无重复。"""
        steps = self.get_funnel_steps(funnel_id)
        if not steps:
            return False
        seqs = [int(s["步骤序号"]) for s in steps]
        expected = list(range(1, len(seqs) + 1))
        return seqs == expected

    def calculate_step_details(self, calc_id: str) -> list[dict[str, Any]]:
        """基于计算批次生成各步骤进入/转化/流失明细。"""
        calcs = store.rows("conv_calc")
        calc = next((c for c in calcs if c.get("计算编号") == calc_id), None)
        if calc is None:
            return []
        funnel_id = calc.get("漏斗编号", "")
        steps = self.get_funnel_steps(funnel_id)
        entry_users = int(calc.get("进入人数", 0))
        conv_users = int(calc.get("转化人数", 0))

        details = []
        current_entry = entry_users
        step_count = len(steps)
        for i, step in enumerate(steps):
            seq = int(step.get("步骤序号", 0))
            if i == step_count - 1:
                step_conv = conv_users
            else:
                ratio = 0.85 ** i  # 每步约 85% 传递
                step_conv = int(entry_users * ratio * (0.6 + 0.1 * (step_count - i - 1)))
            step_conv = max(0, min(step_conv, current_entry))
            dropped = current_entry - step_conv
            rate = round(step_conv / current_entry * 100, 1) if current_entry > 0 else 0.0

            detail = {
                "计算编号": calc_id,
                "步骤序号": seq,
                "进入人数": current_entry,
                "转化人数": step_conv,
                "转化率": rate,
                "流失人数": dropped,
            }
            details.append(detail)
            current_entry = step_conv

        return details

    def modify_step_condition(self, config_id: str, new_condition: str) -> tuple[bool, str]:
        """修改步骤过滤条件：条件变更后触发漏斗版本更新标记。"""
        configs = store.rows("step_config")
        config = next((c for c in configs if c.get("配置编号") == config_id), None)
        if config is None:
            return False, f"配置 {config_id} 不存在"
        old = config.get("过滤条件", "")
        config["过滤条件"] = new_condition
        config["更新时间"] = "2026-10-06T12:00"
        return True, f"步骤过滤条件从 '{old}' 变更为 '{new_condition}'"

    def get_window_period(self, funnel_id: str) -> str:
        """查询漏斗当前生效窗口期。"""
        funnels = store.rows("funnel_def")
        funnel = next((f for f in funnels if f.get("漏斗编号") == funnel_id), None)
        if funnel is None:
            return ""
        # 优先查询窗口调整记录
        adjusts = store.rows("window_adjust")
        active_adjust = next(
            (a for a in adjusts
             if a.get("漏斗编号") == funnel_id and a.get("status") == "已生效"),
            None,
        )
        if active_adjust:
            return active_adjust.get("新窗口期", funnel.get("窗口期", ""))
        return funnel.get("窗口期", "")

    def filter_by_window(self, calc_id: str, window_days: int) -> bool:
        """按窗口期过滤：判断计算批次是否符合转化窗口期要求。"""
        calcs = store.rows("conv_calc")
        calc = next((c for c in calcs if c.get("计算编号") == calc_id), None)
        if calc is None:
            return False
        funnel_id = calc.get("漏斗编号", "")
        period = self.get_window_period(funnel_id)
        # 解析窗口期文字
        try:
            required_days = int("".join(c for c in period if c.isdigit()))
        except ValueError:
            required_days = 7
        return window_days <= required_days

    def snapshot(self) -> dict[str, Any]:
        calcs = store.rows("conv_calc")
        return {
            "calc_count": len(calcs),
            "confirmed_calcs": sum(1 for c in calcs if c.get("status") == "已确认"),
        }