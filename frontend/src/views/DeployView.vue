<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { deployPayload, lifecycleContracts } = storeToRefs(store)

const runtimes = computed(() => (deployPayload.value?.runtimes as Array<Record<string, unknown>>) || [])
const overview = computed(() => (deployPayload.value?.data as Record<string, unknown>) || deployPayload.value || {})
const latestContract = computed(() => {
  const keys = Object.keys(lifecycleContracts.value || {})
  const latestKey = keys[keys.length - 1] || ''
  return latestKey ? (lifecycleContracts.value?.[latestKey] as Record<string, unknown>) || {} : {}
})
const evaluation = computed(() => (latestContract.value?.evaluation as Record<string, unknown> | undefined) || {})
const scoreCard = computed(() => (evaluation.value?.score_card as Record<string, unknown> | undefined) || {})
const promotion = computed(() => (latestContract.value?.promotion as Record<string, unknown> | undefined) || {})
const promotionReady = computed(() => Boolean(promotion.value?.passed ?? false))
const missingEvidence = computed(() => Array.isArray(scoreCard.value?.missing_evidence) ? (scoreCard.value?.missing_evidence as string[]) : [])
</script>

<template>
  <div class="deploy-wrap">
    <h2>Deployment Status</h2>
    <el-row :gutter="16" class="mb">
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <div class="k">Runtime Count</div>
          <div class="v">{{ runtimes.length }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <div class="k">Has Deployment</div>
          <div class="v">{{ String(Boolean(overview?.success ?? true)) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <div class="k">Contract Stage</div>
          <div class="v">{{ String(latestContract.stage ?? '—') }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mb">
      <template #header>Evaluator Snapshot</template>
      <div class="fitness-meta">
        <span>Verdict: {{ String(evaluation.verdict ?? '—') }}</span>
        <span>Passed: {{ String(Boolean(scoreCard.passed ?? false)) }}</span>
        <span>Total: {{ String(scoreCard.total ?? '—') }}</span>
        <span>Reason: {{ String(evaluation.reason ?? scoreCard.reason ?? '—') }}</span>
      </div>
      <div class="fitness-meta" style="margin-top: 8px;">
        <span>Promotion Ready: {{ String(promotionReady) }}</span>
        <span>Runtime Healthy: {{ String(Boolean((overview as Record<string, unknown>).health ?? true)) }}</span>
        <span>Contract Stage: {{ String(latestContract.stage ?? '—') }}</span>
      </div>
      <div class="fitness-meta" style="margin-top: 8px;" v-if="missingEvidence.length">
        <span>Missing Evidence:</span>
        <span>{{ missingEvidence.join(', ') }}</span>
      </div>
    </el-card>

    <el-table :data="runtimes" stripe empty-text="暂无部署记录">
      <el-table-column prop="runtime_id" label="Runtime ID" width="180" />
      <el-table-column prop="project_name" label="Project" />
      <el-table-column prop="status" label="Status" width="120" />
      <el-table-column prop="suggestion_id" label="Suggestion" width="180" />
      <el-table-column prop="evolution_id" label="Evolution" width="180" />
      <el-table-column prop="url" label="URL" />
    </el-table>
  </div>
</template>
