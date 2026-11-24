"""重放校验→计算确定性验证：用相同事件明细重放计算→比对差异→判定确定性。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class ReplayVerification:
    verify_id: str
    calc_id: str
    original_conv: int
    replay_conv: int
    diff_count: int
    is_deterministic: bool
    conclusion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verify_id": self.verify_id,
            "calc_id": self.calc_id,
            "original_conv": self.original_conv,
            "replay_conv": self.replay_conv,
            "diff_count": self.diff_count,
            "is_deterministic": self.is_deterministic,
            "conclusion": self.conclusion,
        }


class ReplayDeterminismFlow:
    """重放校验→计算确定性贯通链路：重放转化计算并比对原结果，验证计算逻辑确定性。"""

    MAX_ACCEPTABLE_DIFF = 0  # 确定性要求零差异
    WARNING_DIFF = 5  # 差异条数超过 5 触发差异待判

    def __init__(self) -> None:
        self._verifications: dict[str, ReplayVerification] = {}
        self._counter = 0

    def verify_calc(self, calc_id: str, replay_result: int) -> ReplayVerification:
        """对指定计算批次执行重放验证。"""
        calcs = store.rows("conv_calc")
        calc = next((c for c in calcs if c.get("计算编号") == calc_id), None)
        if calc is None:
            raise ValueError(f"计算批次 {calc_id} 不存在")

        original = int(calc.get("转化人数", 0))
        diff = abs(replay_result - original)
        self._counter += 1

        is_deterministic = diff == self.MAX_ACCEPTABLE_DIFF
        if is_deterministic:
            conclusion = f"重放转化人数 {replay_result} 与原结果 {original} 一致，计算逻辑确定性通过"
        elif diff <= self.WARNING_DIFF:
            conclusion = f"差异条数 {diff} 在预警范围，需评估是否为延迟登记或事件更正导致"
        else:
            conclusion = f"差异条数 {diff} 超过预警阈值 {self.WARNING_DIFF}，需排查计算逻辑或数据源变更"

        verification = ReplayVerification(
            verify_id=f"RPLV-{self._counter:04d}",
            calc_id=calc_id,
            original_conv=original,
            replay_conv=replay_result,
            diff_count=diff,
            is_deterministic=is_deterministic,
            conclusion=conclusion,
        )
        self._verifications[verification.verify_id] = verification

        # 写入校验记录
        verify_rows = store.rows("replay_verify")
        verify_rows.append({
            "id": max((int(r.get("id", 0)) for r in verify_rows), default=0) + 1,
            "status": "校验通过" if is_deterministic else "差异待判",
            "pending": not is_deterministic,
            "abnormal": not is_deterministic,
            "校验编号": verification.verify_id,
            "计算编号": calc_id,
            "原转化人数": original,
            "重放转化人数": replay_result,
            "差异条数": diff,
            "校验时间": "2026-10-06T05:00",
        })
        return verification

    def get_diff_batches(self) -> list[dict[str, Any]]:
        """返回所有差异待判的重放校验记录。"""
        verify_rows = store.rows("replay_verify")
        return [v for v in verify_rows if v.get("status") == "差异待判"]

    def deterministic_ratio(self) -> float:
        """计算确定性通过的校验比例。"""
        verify_rows = store.rows("replay_verify")
        total = len(verify_rows)
        if total == 0:
            return 0.0
        passed = sum(1 for v in verify_rows if v.get("status") == "校验通过")
        return round(passed / total * 100, 1)

    def compare_diff_count(
        self, verify_id_a: str, verify_id_b: str,
    ) -> dict[str, Any]:
        """比较两条校验记录的差异条数。"""
        verify_rows = store.rows("replay_verify")
        a = next((v for v in verify_rows if v.get("校验编号") == verify_id_a), None)
        b = next((v for v in verify_rows if v.get("校验编号") == verify_id_b), None)
        if not a or not b:
            return {}
        return {
            "a_diff": int(a.get("差异条数", 0)),
            "b_diff": int(b.get("差异条数", 0)),
            "gap": int(a.get("差异条数", 0)) - int(b.get("差异条数", 0)),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "verifications": [v.to_dict() for v in self._verifications.values()],
            "deterministic_ratio": self.deterministic_ratio(),
        }