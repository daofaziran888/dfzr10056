<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "事件接入", "created": 0, "pending": 0, "abnormal": 0}, {"name": "漏斗定义", "created": 0, "pending": 0, "abnormal": 0}, {"name": "步骤配置", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转化计算", "created": 0, "pending": 0, "abnormal": 0}, {"name": "步骤明细", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分群切分", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分群追踪", "created": 0, "pending": 0, "abnormal": 0}, {"name": "留存矩阵", "created": 0, "pending": 0, "abnormal": 0}, {"name": "口径对比", "created": 0, "pending": 0, "abnormal": 0}, {"name": "流失分析", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分群规则", "created": 0, "pending": 0, "abnormal": 0}, {"name": "指标看板", "created": 0, "pending": 0, "abnormal": 0}, {"name": "事件去重", "created": 0, "pending": 0, "abnormal": 0}, {"name": "窗口调整", "created": 0, "pending": 0, "abnormal": 0}, {"name": "路径下钻", "created": 0, "pending": 0, "abnormal": 0}, {"name": "流失预警", "created": 0, "pending": 0, "abnormal": 0}, {"name": "重放校验", "created": 0, "pending": 0, "abnormal": 0}, {"name": "延迟登记", "created": 0, "pending": 0, "abnormal": 0}, {"name": "漏斗版本", "created": 0, "pending": 0, "abnormal": 0}, {"name": "导出任务", "created": 0, "pending": 0, "abnormal": 0}, {"name": "访问审计", "created": 0, "pending": 0, "abnormal": 0}, {"name": "洞察笔记", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
