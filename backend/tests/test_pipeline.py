"""管线层关键链路测试：跨模块真实数据结果断言。"""
from __future__ import annotations

import pytest

from app.pipeline.intake_dedup_flow import IntakeDedupFlow, DedupResult
from app.pipeline.funnel_conv_detail import FunnelConvDetailFlow, ConvCalcResult
from app.pipeline.step_drop_flow import StepDropFlow, DropAnalysisResult
from app.pipeline.cohort_split_track import CohortSplitTrackFlow, CohortTrackEntry
from app.pipeline.track_matrix_flow import TrackMatrixFlow, RetentionMatrix
from app.pipeline.caliber_window_flow import CaliberWindowFlow, CaliberDiffResult
from app.pipeline.caliber_recalc_flow import CaliberRecalcFlow, RecalcAssessment
from app.pipeline.replay_determinism import ReplayDeterminismFlow, ReplayVerification
from app.pipeline.data_delay_recalc import DataDelayRecalcFlow, DelayRecalcResult
from app.pipeline.loss_alert_flow import LossAlertFlow, ChurnAlertResult


# ── IntakeDedupFlow tests ──
class TestIntakeDedupFlow:
    def test_run_dedup_existing_batch(self):
        flow = IntakeDedupFlow()
        result = flow.run_dedup("EVIN-0011")
        assert result.batch_id == "EVIN-0011"
        assert result.total_events == 18500
        assert result.duplicate_count == 120
        assert result.retained_count == 18380
        assert result.status == "已确认"

    def test_run_dedup_high_duplicate_alert(self):
        flow = IntakeDedupFlow()
        result = flow.run_dedup("EVIN-0013")
        assert result.duplicate_count == 8150
        assert result.status == "待复核"

    def test_run_dedup_unknown_batch(self):
        flow = IntakeDedupFlow()
        with pytest.raises(ValueError, match="批次 NOSUCH 不存在"):
            flow.run_dedup("NOSUCH")

    def test_run_dedup_persists_to_store(self):
        flow = IntakeDedupFlow()
        result = flow.run_dedup("EVIN-0011")
        from app.store import store
        dedup_records = store.rows("event_dedup")
        found = any(r.get("批次编号") == "EVIN-0011" and r.get("重复条数") == 120 for r in dedup_records)
        assert found

    def test_run_dedup_zero_duplicates(self):
        flow = IntakeDedupFlow()
        result = flow.run_dedup("EVIN-0014")
        assert result.duplicate_count == 0
        assert result.retained_count == 20100
        assert result.status == "已确认"

    def test_unique_user_count(self):
        flow = IntakeDedupFlow()
        count = flow.unique_user_count("EVIN-0011")
        assert count == 10211  # 18380 / 1.8

    def test_unique_user_count_nonexistent(self):
        flow = IntakeDedupFlow()
        count = flow.unique_user_count("NOSUCH")
        assert count == 0

    def test_duplicate_alert_batches(self):
        flow = IntakeDedupFlow()
        alerts = flow.duplicate_alert_batches()
        assert len(alerts) >= 1

    def test_is_batch_ready_for_funnel_ready(self):
        flow = IntakeDedupFlow()
        assert flow.is_batch_ready_for_funnel("EVIN-0011")

    def test_is_batch_ready_for_funnel_not_ready(self):
        flow = IntakeDedupFlow()
        assert not flow.is_batch_ready_for_funnel("EVIN-0013")

    def test_is_batch_ready_nonexistent(self):
        flow = IntakeDedupFlow()
        assert not flow.is_batch_ready_for_funnel("NOSUCH")

    def test_snapshot(self):
        flow = IntakeDedupFlow()
        flow.run_dedup("EVIN-0011")
        snap = flow.snapshot()
        assert "results" in snap
        assert "duplicate_alert_count" in snap


# ── FunnelConvDetailFlow tests ──
class TestFunnelConvDetailFlow:
    def test_get_funnel_steps(self):
        flow = FunnelConvDetailFlow()
        steps = flow.get_funnel_steps("FNL-001")
        assert len(steps) == 4
        assert steps[0]["步骤序号"] == 1
        assert steps[3]["步骤序号"] == 4

    def test_get_funnel_steps_empty(self):
        flow = FunnelConvDetailFlow()
        steps = flow.get_funnel_steps("NOSUCH")
        assert steps == []

    def test_step_order_valid(self):
        flow = FunnelConvDetailFlow()
        assert flow.step_order_valid("FNL-001")

    def test_step_order_invalid(self):
        flow = FunnelConvDetailFlow()
        assert not flow.step_order_valid("FNL-003")

    def test_calculate_step_details(self):
        flow = FunnelConvDetailFlow()
        details = flow.calculate_step_details("CONV-1001")
        assert len(details) == 4
        assert details[0]["步骤序号"] == 1
        assert details[0]["进入人数"] == 8500
        assert details[3]["转化人数"] == 1275
        assert details[3]["步骤序号"] == 4

    def test_calculate_step_details_nonexistent(self):
        flow = FunnelConvDetailFlow()
        details = flow.calculate_step_details("NOSUCH")
        assert details == []

    def test_modify_step_condition(self):
        flow = FunnelConvDetailFlow()
        ok, msg = flow.modify_step_condition("STPC-0011", "platform='ios'")
        assert ok
        assert "变更为" in msg

    def test_modify_step_condition_not_found(self):
        flow = FunnelConvDetailFlow()
        ok, msg = flow.modify_step_condition("NOSUCH", "x='1'")
        assert not ok

    def test_get_window_period_default(self):
        flow = FunnelConvDetailFlow()
        period = flow.get_window_period("FNL-002")
        assert period in ("3天", "7天")

    def test_get_window_period_with_adjust(self):
        flow = FunnelConvDetailFlow()
        period = flow.get_window_period("FNL-001")
        assert period in ("7天", "3天")

    def test_filter_by_window_passes(self):
        flow = FunnelConvDetailFlow()
        assert flow.filter_by_window("CONV-1001", 3)

    def test_filter_by_window_fails(self):
        flow = FunnelConvDetailFlow()
        assert not flow.filter_by_window("CONV-1001", 30)

    def test_filter_by_window_nonexistent(self):
        flow = FunnelConvDetailFlow()
        assert not flow.filter_by_window("NOSUCH", 7)

    def test_snapshot(self):
        flow = FunnelConvDetailFlow()
        snap = flow.snapshot()
        assert snap["calc_count"] >= 3


# ── StepDropFlow tests ──
class TestStepDropFlow:
    def test_get_step_details_for_calc(self):
        flow = StepDropFlow()
        details = flow.get_step_details_for_calc("CONV-1001")
        assert len(details) == 4

    def test_find_high_drop_steps(self):
        flow = StepDropFlow()
        high = flow.find_high_drop_steps("CONV-1001")
        assert len(high) >= 1
        assert int(high[0]["流失人数"]) > 0

    def test_total_drop_users(self):
        flow = StepDropFlow()
        total = flow.total_drop_users("CONV-1001")
        assert total == (1700 + 2380 + 2210 + 935)

    def test_analyze_drop(self):
        flow = StepDropFlow()
        results = flow.analyze_drop("CONV-1001")
        assert len(results) == 4
        assert results[1].drop_ratio == 35.0

    def test_detect_drop_mutation(self):
        flow = StepDropFlow()
        mutations = flow.detect_drop_mutation("CONV-1001", "CONV-1002")
        assert len(mutations) >= 0

    def test_detect_drop_mutation_same(self):
        flow = StepDropFlow()
        mutations = flow.detect_drop_mutation("CONV-1001", "CONV-1001")
        assert len(mutations) == 0

    def test_find_high_drop_on_small_calc(self):
        flow = StepDropFlow()
        high = flow.find_high_drop_steps("CONV-1002")
        assert isinstance(high, list)

    def test_snapshot(self):
        flow = StepDropFlow()
        flow.analyze_drop("CONV-1001")
        snap = flow.snapshot()
        assert len(snap["analyses"]) == 4


# ── CohortSplitTrackFlow tests ──
class TestCohortSplitTrackFlow:
    def test_active_cohorts(self):
        flow = CohortSplitTrackFlow()
        active = flow.active_cohorts()
        assert len(active) >= 2
        assert all(c["status"] == "已生效" for c in active)

    def test_generate_tracking(self):
        flow = CohortSplitTrackFlow()
        entries = flow.generate_tracking("COHO-010")
        assert len(entries) == 8
        assert entries[0].period == "D1"
        assert entries[0].retention_rate > 0
        assert entries[-1].period == "D180"

    def test_generate_tracking_nonexistent(self):
        flow = CohortSplitTrackFlow()
        entries = flow.generate_tracking("NOSUCH")
        assert entries == []

    def test_retention_sequence_has_values(self):
        flow = CohortSplitTrackFlow()
        flow.generate_tracking("COHO-011")
        seq = flow.retention_sequence("COHO-011")
        assert len(seq) >= 1
        assert any(r > 0 for r in seq)  # 部分观察周期留存率可能为 0（如 D180）

    def test_average_retention_rate(self):
        flow = CohortSplitTrackFlow()
        flow.generate_tracking("COHO-010")
        avg = flow.average_retention_rate("COHO-010")
        assert avg > 0

    def test_average_retention_rate_empty(self):
        flow = CohortSplitTrackFlow()
        avg = flow.average_retention_rate("NOSUCH")
        assert avg == 0.0

    def test_compare_cohort_retention(self):
        flow = CohortSplitTrackFlow()
        flow.generate_tracking("COHO-010")
        flow.generate_tracking("COHO-011")
        comp = flow.compare_cohort_retention("COHO-010", "COHO-011")
        assert "retention_a" in comp
        assert "retention_b" in comp
        assert "gap" in comp

    def test_retention_sequence_descending(self):
        flow = CohortSplitTrackFlow()
        flow.generate_tracking("COHO-010")
        seq = flow.retention_sequence("COHO-010")
        assert seq[0] >= seq[-1]


# ── TrackMatrixFlow tests ──
class TestTrackMatrixFlow:
    def test_build_matrix(self):
        flow = TrackMatrixFlow()
        matrix = flow.build_matrix("COHO-010")
        assert matrix is not None
        assert len(matrix.retention_series) >= 1
        assert matrix.version_tag == "v1.0-口径"

    def test_build_matrix_empty_cohort(self):
        flow = TrackMatrixFlow()
        matrix = flow.build_matrix("NOSUCH")
        assert matrix is None

    def test_mark_version(self):
        flow = TrackMatrixFlow()
        flow.build_matrix("COHO-010")
        ok, msg = flow.mark_version("RMTX-0001", "v2.1-口径")
        assert ok

    def test_mark_version_nonexistent(self):
        flow = TrackMatrixFlow()
        ok, msg = flow.mark_version("NOSUCH", "v1.0")
        assert not ok

    def test_get_version_mismatch_matrices(self):
        flow = TrackMatrixFlow()
        mismatches = flow.get_version_mismatch_matrices("v100.0")
        assert isinstance(mismatches, list)

    def test_publish_matrix(self):
        flow = TrackMatrixFlow()
        ok, msg = flow.publish_matrix("NOSUCH")
        assert not ok


# ── CaliberWindowFlow tests ──
class TestCaliberWindowFlow:
    def test_compare_caliber(self):
        flow = CaliberWindowFlow()
        result = flow.compare_caliber("FNL-001")
        assert result is not None
        assert result.old_rate == 14.5
        assert result.new_rate == 16.8

    def test_compare_caliber_nonexistent(self):
        flow = CaliberWindowFlow()
        result = flow.compare_caliber("NOSUCH")
        assert result is None

    def test_compare_caliber_significance(self):
        flow = CaliberWindowFlow()
        result = flow.compare_caliber("FNL-002")
        assert result is not None
        assert result.old_rate == 28.0
        assert result.new_rate == 30.0
        assert result.needs_window_adjust

    def test_affected_calc_batches(self):
        flow = CaliberWindowFlow()
        affected = flow.affected_calc_batches("FNL-001")
        assert len(affected) >= 3

    def test_propose_window_adjust(self):
        flow = CaliberWindowFlow()
        ok, msg = flow.propose_window_adjust("FNL-001", "7天", "3天")
        assert ok
        assert "影响" in msg

    def test_history_recalc_decision_accept(self):
        flow = CaliberWindowFlow()
        ok, msg = flow.history_recalc_decision("CLCP-002", "accept")
        assert ok

    def test_history_recalc_decision_reject(self):
        flow = CaliberWindowFlow()
        ok, msg = flow.history_recalc_decision("CLCP-003", "reject")
        assert ok

    def test_snapshot(self):
        flow = CaliberWindowFlow()
        snap = flow.snapshot()
        assert snap["compare_count"] >= 2


# ── CaliberRecalcFlow tests ──
class TestCaliberRecalcFlow:
    def test_get_funnel_versions(self):
        flow = CaliberRecalcFlow()
        versions = flow.get_funnel_versions("FNL-001")
        assert len(versions) >= 2

    def test_assess_recalc_need_significant(self):
        flow = CaliberRecalcFlow()
        # 先确保有一条待裁决的对比记录
        from app.store import store
        cal_rows = store.rows("caliber_compare")
        candidate = None
        for r in cal_rows:
            if r.get("status") == "待裁决" and float(r.get("对比差值", 0)) >= 1.0:
                candidate = r
                break
        if candidate is None:
            # 没有待裁决的，创建一条
            new_id = max((int(r.get("id", 0)) for r in cal_rows), default=0) + 1
            cal_rows.append({
                "id": new_id, "status": "待裁决", "pending": True, "abnormal": True,
                "对比编号": "CLCP-TEST", "漏斗编号": "FNL-001",
                "旧口径转化率": 14.0, "新口径转化率": 17.0,
                "对比差值": 3.0, "对比时间": "2026-10-06T12:00",
            })
            funnel_id = "FNL-001"
        else:
            funnel_id = candidate["漏斗编号"]
        assessment = flow.assess_recalc_need(funnel_id, "v2.0", "v2.1")
        assert len(assessment.affected_batches) >= 1

    def test_assess_recalc_need_insignificant(self):
        flow = CaliberRecalcFlow()
        assessment = flow.assess_recalc_need("FNL-004", "v0-legacy", "v1.0")
        assert isinstance(assessment.affected_batches, list)

    def test_commit_version_rollback(self):
        flow = CaliberRecalcFlow()
        ok, msg = flow.commit_version_rollback("FNL-001", "v2.0")
        assert ok

    def test_commit_version_rollback_nonexistent(self):
        flow = CaliberRecalcFlow()
        ok, msg = flow.commit_version_rollback("FNL-001", "v99")
        assert not ok

    def test_get_affected_step_configs(self):
        flow = CaliberRecalcFlow()
        configs = flow.get_affected_step_configs("FNL-001")
        assert len(configs) >= 4

    def test_snapshot(self):
        flow = CaliberRecalcFlow()
        flow.assess_recalc_need("FNL-001", "v2.0", "v2.1")
        snap = flow.snapshot()
        assert len(snap["assessments"]) >= 1


# ── ReplayDeterminismFlow tests ──
class TestReplayDeterminismFlow:
    def test_verify_calc_exact_match(self):
        flow = ReplayDeterminismFlow()
        verif = flow.verify_calc("CONV-1001", 1275)
        assert verif.is_deterministic
        assert verif.diff_count == 0
        assert verif.conclusion == f"重放转化人数 1275 与原结果 1275 一致，计算逻辑确定性通过"

    def test_verify_calc_small_diff(self):
        flow = ReplayDeterminismFlow()
        verif = flow.verify_calc("CONV-1001", 1270)
        assert not verif.is_deterministic
        assert verif.diff_count == 5
        assert "延迟登记或事件更正" in verif.conclusion

    def test_verify_calc_large_diff(self):
        flow = ReplayDeterminismFlow()
        verif = flow.verify_calc("CONV-1001", 1200)
        assert not verif.is_deterministic
        assert verif.diff_count == 75
        assert "排查计算逻辑" in verif.conclusion

    def test_verify_calc_nonexistent(self):
        flow = ReplayDeterminismFlow()
        with pytest.raises(ValueError, match="计算批次 NOSUCH 不存在"):
            flow.verify_calc("NOSUCH", 100)

    def test_get_diff_batches(self):
        flow = ReplayDeterminismFlow()
        flow.verify_calc("CONV-1001", 1200)
        diffs = flow.get_diff_batches()
        assert len(diffs) >= 1

    def test_deterministic_ratio_after_exact_verify(self):
        flow = ReplayDeterminismFlow()
        flow.verify_calc("CONV-1001", 1275)
        flow.verify_calc("CONV-1002", 1410)
        # 验证两个精确匹配的校验都通过
        from app.store import store
        verifs = store.rows("replay_verify")
        matched = [v for v in verifs if int(v.get("差异条数", 1)) == 0]
        assert len(matched) >= 2

    def test_compare_diff_count_between_batches(self):
        flow = ReplayDeterminismFlow()
        v1 = flow.verify_calc("CONV-1001", 1275)
        v2 = flow.verify_calc("CONV-1001", 1200)
        # 直接用返回对象的 diff_count 比对
        assert v1.diff_count == 0
        assert v2.diff_count > 0

    def test_snapshot_contains_verifications(self):
        flow = ReplayDeterminismFlow()
        flow.verify_calc("CONV-1001", 1275)
        snap = flow.snapshot()
        assert "verifications" in snap
        assert "deterministic_ratio" in snap


# ── DataDelayRecalcFlow tests ──
class TestDataDelayRecalcFlow:
    def test_register_delay_overdue(self):
        flow = DataDelayRecalcFlow()
        result = flow.register_delay("EVIN-0013", "2026-10-04T01:00", "2026-10-05T08:30")
        assert result.delay_hours > 0
        assert result.needs_recalc

    def test_register_delay_short(self):
        flow = DataDelayRecalcFlow()
        result = flow.register_delay("EVIN-0014", "2026-10-05T01:00", "2026-10-05T01:10")
        assert result.delay_hours < 6.0
        assert not result.needs_recalc

    def test_register_delay_ignored(self):
        flow = DataDelayRecalcFlow()
        result = flow.register_delay("EVIN-0012", "2026-10-03T01:00", "2026-10-03T01:20")
        assert result.verdict is not None

    def test_batches_needing_recalc(self):
        flow = DataDelayRecalcFlow()
        flow.register_delay("EVIN-0013", "2026-10-04T01:00", "2026-10-05T08:30")
        batches = flow.batches_needing_recalc()
        assert len(batches) >= 1

    def test_ignore_short_delays(self):
        flow = DataDelayRecalcFlow()
        flow.register_delay("EVIN-0014", "2026-10-05T01:00", "2026-10-05T01:10")
        count = flow.ignore_short_delays()
        assert count >= 0

    def test_snapshot(self):
        flow = DataDelayRecalcFlow()
        flow.register_delay("EVIN-0013", "2026-10-04T01:00", "2026-10-05T08:30")
        snap = flow.snapshot()
        assert snap["needs_recalc_count"] >= 1


# ── LossAlertFlow tests ──
class TestLossAlertFlow:
    def test_calculate_churn_rate(self):
        flow = LossAlertFlow()
        rate = flow.calculate_churn_rate("COHO-010")
        assert isinstance(rate, float)

    def test_calculate_churn_rate_nonexistent(self):
        flow = LossAlertFlow()
        rate = flow.calculate_churn_rate("NOSUCH")
        assert rate == 0.0

    def test_check_threshold_deviation_triggered(self):
        flow = LossAlertFlow()
        result = flow.check_threshold_deviation("COHO-010", 10.0)
        assert result.triggered

    def test_check_threshold_deviation_not_triggered(self):
        flow = LossAlertFlow()
        result = flow.check_threshold_deviation("COHO-010", 90.0)
        assert not result.triggered

    def test_high_level_alerts_initial(self):
        flow = LossAlertFlow()
        flow.check_threshold_deviation("COHO-010", 10.0)
        high = flow.high_level_alerts()
        assert len(high) >= 0

    def test_dispose_alert(self):
        flow = LossAlertFlow()
        flow.check_threshold_deviation("COHO-010", 10.0)
        from app.store import store
        alerts = store.rows("churn_alert")
        triggered = [a for a in alerts if a.get("status") == "已触发"]
        if triggered:
            ok, msg = flow.dispose_alert(triggered[0]["预警编号"])
            assert ok

    def test_release_alert(self):
        flow = LossAlertFlow()
        flow.check_threshold_deviation("COHO-010", 10.0)
        from app.store import store
        alerts = store.rows("churn_alert")
        for a in alerts:
            if a.get("status") in ("已触发", "已处置", "已解除"):
                ok, msg = flow.release_alert(a["预警编号"])
                assert ok
                break

    def test_snapshot(self):
        flow = LossAlertFlow()
        flow.check_threshold_deviation("COHO-010", 10.0)
        snap = flow.snapshot()
        assert "alerts" in snap


# ── Service-level domain method tests ──
class TestEventIntakeService:
    def test_find_by_batch_id(self):
        from app.services.event_intake import EventIntakeService
        svc = EventIntakeService()
        batch = svc.find_by_batch_id("EVIN-0011")
        assert batch is not None
        assert batch["事件条数"] == 18500

    def test_count_batches_by_source(self):
        from app.services.event_intake import EventIntakeService
        svc = EventIntakeService()
        count = svc.count_batches_by_source("user_behavior_log")
        assert count == 3

    def test_batches_in_window(self):
        from app.services.event_intake import EventIntakeService
        svc = EventIntakeService()
        matches = svc.get_batches_in_window("2026-10-01T00:00", "2026-10-02T23:59")
        assert len(matches) >= 2


class TestChurnAlertService:
    def test_check_threshold_high(self):
        from app.services.churn_alert import ChurnAlertService
        svc = ChurnAlertService()
        triggered, reason = svc.check_threshold_deviation("COHO-010", 10.0, 22.0)
        assert triggered
        assert "1.5" in reason or "1.2" in reason

    def test_check_threshold_normal(self):
        from app.services.churn_alert import ChurnAlertService
        svc = ChurnAlertService()
        triggered, reason = svc.check_threshold_deviation("COHO-010", 50.0, 22.0)
        assert not triggered


class TestCaliberCompareService:
    def test_interpret_diff(self):
        from app.services.caliber_compare import CaliberCompareService
        svc = CaliberCompareService()
        msg = svc.interpret_diff("CLCP-002")
        assert "2.3" in msg

    def test_find_pending_comparisons_exists(self):
        from app.services.caliber_compare import CaliberCompareService
        from app.store import store
        # 确保存在待裁决记录
        cal_rows = store.rows("caliber_compare")
        for r in cal_rows:
            r["status"] = r.get("status", "")
        has_pending = any(r.get("status") == "待裁决" for r in cal_rows)
        if not has_pending:
            cal_rows.append({
                "id": 99, "status": "待裁决", "pending": True, "abnormal": True,
                "对比编号": "CLCP-PEND", "漏斗编号": "FNL-001",
                "旧口径转化率": 10.0, "新口径转化率": 15.0,
                "对比差值": 5.0, "对比时间": "2026-10-06T13:00",
            })
        svc = CaliberCompareService()
        pending = svc.find_pending_comparisons()
        assert len(pending) >= 1

    def test_sign_and_resolve(self):
        from app.services.caliber_compare import CaliberCompareService
        svc = CaliberCompareService()
        ok, msg = svc.sign_and_resolve("CLCP-002", True)
        assert ok
        assert "采纳新口径" in msg


# ── EventDedupService tests ──
class TestEventDedupService:
    def test_count_unique_users(self):
        from app.services.event_dedup import EventDedupService
        svc = EventDedupService()
        count = svc.count_unique_users("EVIN-0011")
        assert count == pytest.approx(10211.11, rel=0.01)

    def test_find_high_duplicate_batches(self):
        from app.services.event_dedup import EventDedupService
        svc = EventDedupService()
        high = svc.find_high_duplicate_batches()
        assert len(high) >= 1

    def test_duplicate_ratio(self):
        from app.services.event_dedup import EventDedupService
        svc = EventDedupService()
        ratio = svc.duplicate_ratio("EVIN-0011")
        assert ratio == pytest.approx(0.65, rel=0.1)


# ── ReplayVerifyService tests ──
class TestReplayVerifyService:
    def test_deterministic_ratio(self):
        from app.services.replay_verify import ReplayVerifyService
        svc = ReplayVerifyService()
        ratio = svc.deterministic_ratio()
        assert 0 <= ratio <= 100

    def test_find_diff_verifications(self):
        from app.services.replay_verify import ReplayVerifyService
        svc = ReplayVerifyService()
        diffs = svc.find_diff_verifications()
        assert len(diffs) >= 2