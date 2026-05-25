<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { apiPlatformDeploy } from '@/api/platform'
import { apiLifecycleContract } from '@/api/lifecycle'
import { apiStatus } from '@/api/execution'

const deployPayload = ref<Record<string, unknown> | null>(null)
const latestContract = ref<Record<string, unknown> | null>(null)

async function loadData() {
  deployPayload.value = await apiPlatformDeploy()
  const status = await apiStatus()
  const execId = String(status?.primary_execution?.execution_id ?? status?.executions?.[0]?.execution_id ?? '')
  if (execId) {
    latestContract.value = await apiLifecycleContract(execId)
  }
}

onMounted(() => void loadData())

const runtimes = computed(() => (deployPayload.value?.data?.runtimes as Array<Record<string, unknown>>) || (deployPayload.value?.runtimes as Array<Record<string, unknown>>) || [])
const overview = computed(() => (deployPayload.value?.data as Record<string, unknown>) || deployPayload.value || {})
const contractData = computed(() => latestContract.value?.data as Record<string, unknown> | undefined || {})
const evaluation = computed(() => (contractData.value?.evaluation as Record<string, unknown> | undefined) || {})
const scoreCard = computed(() => (evaluation.value?.score_card as Record<string, unknown> | undefined) || {})
const promotion = computed(() => (contractData.value?.promotion as Record<string, unknown> | undefined) || {})
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
          <div class="v">{{ String(contractData.stage ?? '—') }}</div>
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
        <span>Contract Stage: {{ String(contractData.stage ?? '—') }}</span>
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