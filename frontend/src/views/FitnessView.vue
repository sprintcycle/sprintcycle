<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { apiPlatformFitness } from '@/api/platform'
import { apiPlatformDeploy } from '@/api/platform'
import { apiLifecycleContract } from '@/api/lifecycle'
import { apiStatus } from '@/api/execution'

const fitness = ref<Record<string, unknown> | null>(null)
const deployPayload = ref<Record<string, unknown> | null>(null)
const latestContract = ref<Record<string, unknown> | null>(null)

async function loadData() {
  fitness.value = await apiPlatformFitness()
  deployPayload.value = await apiPlatformDeploy()
  const status = await apiStatus()
  const execId = String(status?.primary_execution?.execution_id ?? status?.executions?.[0]?.execution_id ?? '')
  if (execId) {
    latestContract.value = await apiLifecycleContract(execId)
  }
}

onMounted(() => void loadData())

const score = computed(() => Number(fitness.value?.data?.overall ?? 0))
const fitnessSummary = computed(() => ({
  deployments: Array.isArray(deployPayload.value?.data?.runtimes) ? deployPayload.value?.data?.runtimes.length : 0,
  promoted: 0,
  contracts: latestContract.value ? 1 : 0,
}))

const contractData = computed(() => latestContract.value?.data as Record<string, unknown> | undefined || {})
const review = computed(() => (contractData.value?.evaluation as Record<string, unknown> | undefined) || {})
const scoreCard = computed(() => (review.value?.score_card as Record<string, unknown> | undefined) || {})
const passed = computed(() => Boolean(scoreCard.value?.passed ?? review.value?.passed ?? false))
const verdict = computed(() => String(review.value?.verdict ?? (scoreCard.value?.passed ? 'passed' : 'pending')))
const reason = computed(() => String(review.value?.reason ?? scoreCard.value?.reason ?? '—'))
const weights = computed(() => (scoreCard.value?.weights as Record<string, unknown> | undefined) || {})

function scoreColor(s: number): string {
  if (s >= 80) return '#22c55e'
  if (s >= 60) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <div class="fitness-wrap">
    <h2>Fitness</h2>
    <el-card shadow="never" class="fitness-card">
      <div class="fitness-score" :style="{ color: scoreColor(score) }">{{ score }}</div>
      <div class="fitness-title">Fitness Score</div>
      <div class="fitness-desc">综合评估平台健康状况</div>
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

    <el-table :data="[]" stripe empty-text="暂无问题" class="fitness-table">
      <el-table-column prop="severity" label="Severity" width="120" />
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="detail" label="Detail" />
    </el-table>
  </div>
</template>