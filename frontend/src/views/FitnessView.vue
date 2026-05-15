<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { diagnoseScore, diagnoseTitle, diagnoseDesc, diagnoseIssues, deployPayload, promotionLog, lifecycleContracts } = storeToRefs(store)

const score = computed(() => diagnoseScore.value ?? 0)
const fitnessSummary = computed(() => ({
  deployments: Array.isArray(deployPayload.value?.runtimes) ? deployPayload.value?.runtimes.length : 0,
  promoted: promotionLog.value.length,
  contracts: Object.keys(lifecycleContracts.value || {}).length,
}))

const latestContract = computed(() => {
  const keys = Object.keys(lifecycleContracts.value || {})
  const key = keys[keys.length - 1] || ''
  return (key ? lifecycleContracts.value?.[key] : null) as Record<string, unknown> | null
})

const review = computed(() => (latestContract.value?.evaluation as Record<string, unknown> | undefined) || {})
const scoreCard = computed(() => (review.value?.score_card as Record<string, unknown> | undefined) || {})
const passed = computed(() => Boolean(scoreCard.value?.passed ?? review.value?.passed ?? false))
const verdict = computed(() => String(review.value?.verdict ?? (scoreCard.value?.passed ? 'passed' : 'pending')))
const reason = computed(() => String(review.value?.reason ?? scoreCard.value?.reason ?? '—'))
const weights = computed(() => (scoreCard.value?.weights as Record<string, unknown> | undefined) || {})
</script>

<template>
  <div class="fitness-wrap">
    <h2>Fitness</h2>
    <el-card shadow="never" class="fitness-card">
      <div class="fitness-score" :style="{ color: store.scoreColor(score) }">{{ score }}</div>
      <div class="fitness-title">{{ diagnoseTitle }}</div>
      <div class="fitness-desc">{{ diagnoseDesc }}</div>
      <div class="fitness-meta">
        <span>Deployments: {{ fitnessSummary.deployments }}</span>
        <span>Promoted: {{ fitnessSummary.promoted }}</span>
        <span>Contracts: {{ fitnessSummary.contracts }}</span>
      </div>
    </el-card>

    <el-card shadow="never" class="fitness-card" v-if="latestContract">
      <template #header>Evaluator Review</template>
      <div class="fitness-meta">
        <span>Verdict: {{ verdict }}</span>
        <span>Passed: {{ String(passed) }}</span>
        <span>Reason: {{ reason }}</span>
      </div>
      <div class="fitness-meta">
        <span>Functionality: {{ String(scoreCard.functionality ?? '—') }}</span>
        <span>Structure: {{ String(scoreCard.structure ?? '—') }}</span>
        <span>Evidence: {{ String(scoreCard.evidence ?? '—') }}</span>
        <span>Delivery: {{ String(scoreCard.delivery ?? '—') }}</span>
        <span>Total: {{ String(scoreCard.total ?? '—') }}</span>
      </div>
      <div class="fitness-meta">
        <span>W/functionality: {{ String(weights.functionality ?? '—') }}</span>
        <span>W/structure: {{ String(weights.structure ?? '—') }}</span>
        <span>W/evidence: {{ String(weights.evidence ?? '—') }}</span>
        <span>W/delivery: {{ String(weights.delivery ?? '—') }}</span>
      </div>
    </el-card>

    <el-table :data="diagnoseIssues" stripe empty-text="暂无问题" class="fitness-table">
      <el-table-column prop="severity" label="Severity" width="120" />
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="detail" label="Detail" />
    </el-table>
  </div>
</template>
