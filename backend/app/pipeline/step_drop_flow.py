"""步骤明细→流失分析：抽取步骤流失数据→计算流失占比→生成分析结论。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class DropAnalysisResult:
    analysis_id: str
    calc_id: str
    step_seq: int
    drop_count: int
    drop_ratio: float
    conclusion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "calc_id": self.calc_id,
            "step_seq": self.step_seq,
            "drop_count": self.drop_count,
            "drop_ratio": self.drop_ratio,
            "conclusion": self.conclusion,
        }


class StepDropFlow:
    """步骤明细→流失分析贯通链路：从步骤明细中定位流失集中的步骤，计算流失占比与结论。"""

    DROP_RATIO_ALERT = 40.0  # 流失占比超过 40% 标记为高流失
    DROP_MUTATION_THRESHOLD = 15.0  # 流失占比突变阈值

    def __init__(self) -> None:
        self._analyses: dict[str, DropAnalysisResult] = {}
        self._counter = 0

    def get_step_details_for_calc(self, calc_id: str) -> list[dict[str, Any]]:
        """获取指定计算批次的所有步骤明细。"""
        details = store.rows("step_detail")
        return [d for d in details if d.get("计算编号") == calc_id]

    def find_high_drop_steps(self, calc_id: str) -> list[dict[str, Any]]:
        """找出流失占比超过阈值的步骤。"""
        details = self.get_step_details_for_calc(calc_id)
        high_drop = []
        for d in details:
            dropped = int(d.get("流失人数", 0))
            entered = int(d.get("进入人数", 0))
            ratio = (dropped / entered * 100) if entered > 0 else 0
            if ratio >= self.DROP_RATIO_ALERT:
                high_drop.append(d)
        return high_drop

    def total_drop_users(self, calc_id: str) -> int:
        """统计该计算批次各步骤流失总人数。"""
        details = self.get_step_details_for_calc(calc_id)
        return sum(int(d.get("流失人数", 0)) for d in details)

    def analyze_drop(self, calc_id: str) -> list[DropAnalysisResult]:
        """对计算批次所有步骤执行流失分析。"""
        details = self.get_step_details_for_calc(calc_id)
        results: list[DropAnalysisResult] = []
        for d in details:
            seq = int(d.get("步骤序号", 0))
            dropped = int(d.get("流失人数", 0))
            entered = int(d.get("进入人数", 0))
            ratio = round(dropped / entered * 100, 1) if entered > 0 else 0.0
            if ratio >= self.DROP_RATIO_ALERT:
                conclusion = f"步骤 {seq} 流失占比 {ratio}% 超过阈值 {self.DROP_RATIO_ALERT}%，为高流失步骤"
            else:
                conclusion = f"步骤 {seq} 流失占比 {ratio}% 在正常范围"
            result = DropAnalysisResult(
                analysis_id=f"DROP-{len(results)+1:04d}",
                calc_id=calc_id,
                step_seq=seq,
                drop_count=dropped,
                drop_ratio=ratio,
                conclusion=conclusion,
            )
            results.append(result)
            self._analyses[result.analysis_id] = result
        return results

    def detect_drop_mutation(
        self, calc_id_a: str, calc_id_b: str,
    ) -> list[dict[str, Any]]:
        """检测两批次间流失占比突变：超过阈值的步骤触发事件质量排查。"""
        details_a = self.get_step_details_for_calc(calc_id_a)
        details_b = self.get_step_details_for_calc(calc_id_b)
        mutations = []
        steps_a = {int(d["步骤序号"]): d for d in details_a}
        steps_b = {int(d["步骤序号"]): d for d in details_b}
        for seq in sorted(set(steps_a) | set(steps_b)):
            d_a = steps_a.get(seq)
            d_b = steps_b.get(seq)
            if d_a and d_b:
                entered_a = int(d_a.get("进入人数", 0))
                entered_b = int(d_b.get("进入人数", 0))
                ratio_a = (int(d_a.get("流失人数", 0)) / entered_a * 100) if entered_a > 0 else 0
                ratio_b = (int(d_b.get("流失人数", 0)) / entered_b * 100) if entered_b > 0 else 0
                mutation = abs(ratio_b - ratio_a)
                if mutation >= self.DROP_MUTATION_THRESHOLD:
                    mutations.append({
                        "step_seq": seq,
                        "ratio_a": round(ratio_a, 1),
                        "ratio_b": round(ratio_b, 1),
                        "mutation": round(mutation, 1),
                        "trigger_quality_check": True,
                    })
        return mutations

    def snapshot(self) -> dict[str, Any]:
        return {
            "analyses": [a.to_dict() for a in self._analyses.values()],
        }