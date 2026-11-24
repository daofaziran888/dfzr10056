<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">砂漏工坊 · 转化漏斗与分群留存分析平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向事件明细接入、漏斗步骤定义、转化率计算、分群切分、留存矩阵与口径对比的用户行为分析平台。</span>
        <span class="head-user">当前值班：数据工程组</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
const navItems = [{ label: "运营概览", path: "/" }, { label: "事件接入", path: "/event_intake" }, { label: "漏斗定义", path: "/funnel_def" }, { label: "步骤配置", path: "/step_config" }, { label: "转化计算", path: "/conv_calc" }, { label: "步骤明细", path: "/step_detail" }, { label: "分群切分", path: "/cohort_split" }, { label: "分群追踪", path: "/cohort_track" }, { label: "留存矩阵", path: "/retain_matrix" }, { label: "口径对比", path: "/caliber_compare" }, { label: "流失分析", path: "/drop_analysis" }, { label: "分群规则", path: "/segment_rule" }, { label: "指标看板", path: "/metric_board" }, { label: "事件去重", path: "/event_dedup" }, { label: "窗口调整", path: "/window_adjust" }, { label: "路径下钻", path: "/path_drill" }, { label: "流失预警", path: "/churn_alert" }, { label: "重放校验", path: "/replay_verify" }, { label: "延迟登记", path: "/data_delay" }, { label: "漏斗版本", path: "/funnel_version" }, { label: "导出任务", path: "/export_task" }, { label: "访问审计", path: "/access_audit" }, { label: "洞察笔记", path: "/insight_note" }]
</script>
