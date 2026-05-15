<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { apiDashboardLifecycleContract, apiDashboardLifecycleContractReview } from '@/api'

const executionId = ref('')
const loading = ref(false)
const reviewLoading = ref(false)
const contract = ref<Record<string, unknown> | null>(null)
const reviewResult = ref<Record<string, unknown> | null>(null)

const latest = computed(() => contract.value || {})
const evaluation = computed(() => (latest.value?.evaluation as Record<string, unknown> | undefined) || {})
const scoreCard = computed(() => (evaluation.value?.score_card as Record<string, unknown> | undefined) || {})
const missingEvidence = computed(() => Array.isArray(scoreCard.value?.missing_evidence) ? (scoreCard.value?.missing_evidence as string[]) : [])

async function loadContract() {
  if (!executionId.value) return
  loading.value = true
  try {
    const res = await apiDashboardLifecycleContract(executionId.value)
    contract.value = (res.data as Record<string, unknown>) || res
    reviewResult.value = null
  } finally {
    loading.value = false
  }
}

async function runReview() {
  if (!executionId.value) return
  reviewLoading.value = true
  try {
    const res = await apiDashboardLifecycleContractReview(executionId.value, {})
    reviewResult.value = (res.data as Record<string, unknown>) || res
    await loadContract()
    ElMessage.success('Contract review completed')
  } finally {
    reviewLoading.value = false
  }
}

watch(executionId, () => {
  contract.value = null
  reviewResult.value = null
})
</script>

<template>
  <div class="contract-review">
    <div class="hero">
      <div>
        <div class="eyebrow">SprintCycle · Contract Review</div>
        <h1>Contract Review</h1>
        <p class="subtitle">查看单个 execution 的 contract、evaluation、missing evidence 与 review 结果。</p>
      </div>
    </div>

    <el-card shadow="never" class="panel-card mb">
      <template #header>查询与评审</template>
      <div class="actions">
        <el-input v-model="executionId" placeholder="输入 execution_id" clearable style="max-width: 420px" />
        <el-button type="primary" :loading="loading" @click="loadContract">加载 Contract</el-button>
        <el-button :loading="reviewLoading" :disabled="!executionId" @click="runReview">重新评审</el-button>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card mb">
          <template #header>Evaluation Summary</template>
          <div class="summary-grid">
            <div><span>Verdict</span><b>{{ String(evaluation.verdict ?? '—') }}</b></div>
            <div><span>Reason</span><b>{{ String(evaluation.reason ?? '—') }}</b></div>
            <div><span>Passed</span><b>{{ String(Boolean(scoreCard.passed ?? false)) }}</b></div>
            <div><span>Total</span><b>{{ String(scoreCard.total ?? '—') }}</b></div>
            <div><span>Functionality</span><b>{{ String(scoreCard.functionality ?? '—') }}</b></div>
            <div><span>Structure</span><b>{{ String(scoreCard.structure ?? '—') }}</b></div>
            <div><span>Evidence</span><b>{{ String(scoreCard.evidence ?? '—') }}</b></div>
            <div><span>Delivery</span><b>{{ String(scoreCard.delivery ?? '—') }}</b></div>
          </div>
          <div v-if="missingEvidence.length" class="missing-box">
            <div class="missing-title">Missing Evidence</div>
            <div class="missing-list">{{ missingEvidence.join(', ') }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card mb">
          <template #header>Review Result</template>
          <pre class="json-box">{{ JSON.stringify(reviewResult || contract, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel-card" v-if="contract">
      <template #header>Contract Snapshot</template>
      <pre class="json-box">{{ JSON.stringify(contract, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<style scoped>
.contract-review {
  display: grid;
  gap: 16px;
}
.hero {
  display: flex;
  justify-content: space-between;
  align-items: start;
}
.eyebrow {
  color: #60a5fa;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.subtitle {
  color: #94a3b8;
  margin: 0;
}
.mb { margin-bottom: 16px; }
.panel-card { background: #111827; border-color: #334155; }
.actions { display: flex; gap: 12px; flex-wrap: wrap; }
.summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.summary-grid span { color: #94a3b8; font-size: 12px; }
.summary-grid b { color: #e2e8f0; display: block; margin-top: 4px; }
.json-box { margin: 0; white-space: pre-wrap; color: #cbd5e1; background: #0f172a; padding: 12px; border-radius: 12px; max-height: 520px; overflow: auto; }
.missing-box { margin-top: 12px; padding: 12px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; }
.missing-title { color: #fca5a5; font-weight: 600; margin-bottom: 6px; }
.missing-list { color: #fecaca; }
</style>
