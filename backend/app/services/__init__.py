"""领域服务注册表：通用资源路由按模块 key 分派到独立业务服务。"""
from __future__ import annotations

from app.services.base import BaseModuleService
from app.services.event_intake import EventIntakeService
from app.services.funnel_def import FunnelDefService
from app.services.step_config import StepConfigService
from app.services.conv_calc import ConvCalcService
from app.services.step_detail import StepDetailService
from app.services.cohort_split import CohortSplitService
from app.services.cohort_track import CohortTrackService
from app.services.retain_matrix import RetainMatrixService
from app.services.caliber_compare import CaliberCompareService
from app.services.drop_analysis import DropAnalysisService
from app.services.segment_rule import SegmentRuleService
from app.services.metric_board import MetricBoardService
from app.services.event_dedup import EventDedupService
from app.services.window_adjust import WindowAdjustService
from app.services.path_drill import PathDrillService
from app.services.churn_alert import ChurnAlertService
from app.services.replay_verify import ReplayVerifyService
from app.services.data_delay import DataDelayService
from app.services.funnel_version import FunnelVersionService
from app.services.export_task import ExportTaskService
from app.services.access_audit import AccessAuditService
from app.services.insight_note import InsightNoteService

SERVICES: dict[str, BaseModuleService] = {
    "event_intake": EventIntakeService(),
    "funnel_def": FunnelDefService(),
    "step_config": StepConfigService(),
    "conv_calc": ConvCalcService(),
    "step_detail": StepDetailService(),
    "cohort_split": CohortSplitService(),
    "cohort_track": CohortTrackService(),
    "retain_matrix": RetainMatrixService(),
    "caliber_compare": CaliberCompareService(),
    "drop_analysis": DropAnalysisService(),
    "segment_rule": SegmentRuleService(),
    "metric_board": MetricBoardService(),
    "event_dedup": EventDedupService(),
    "window_adjust": WindowAdjustService(),
    "path_drill": PathDrillService(),
    "churn_alert": ChurnAlertService(),
    "replay_verify": ReplayVerifyService(),
    "data_delay": DataDelayService(),
    "funnel_version": FunnelVersionService(),
    "export_task": ExportTaskService(),
    "access_audit": AccessAuditService(),
    "insight_note": InsightNoteService(),
}


def service_for(module: str) -> BaseModuleService | None:
    return SERVICES.get(module)
