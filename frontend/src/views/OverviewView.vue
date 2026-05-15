<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiDashboardFitness, apiDashboardGovernance, apiDashboardDeploy, apiDashboardLifecycleContract, apiPlatformSummary } from '@/api'

const router = useRouter()
const loading = ref(false)
const summary = ref<Record<string, unknown> | null>(null)
const fitness = ref<Record<string, unknown> | null>(null)
const governance = ref<Record<string, unknown> | null>(null)
const deploy = ref<Record<string, unknown> | null>(null)
const lifecycleContract = ref<Record<string, unknown> | null>(null)

async function refresh() {
  loading.value = true
  try {
    summary.value = await apiPlatformSummary()
    fitness.value = await apiDashboardFitness()
    governance.value = await apiDashboardGovernance()
    deploy.value = await apiDashboardDeploy()
    const primary = summary.value?.executions_overview as Record<string, unknown> | undefined
    const execId = typeof primary?.primary_execution === 'object' ? String((primary?.primary_execution as Record<string, unknown>)?.execution_id ?? '') : ''
    lifecycleContract.value = execId ? await apiDashboardLifecycleContract(execId) : null
  } finally {
    loading.value = false
  }
}

onMounted(() => void refresh())

const executions = computed(() => {
  const ex = summary.value?.executions_overview as Record<string, unknown> | undefined
  return Array.isArray(ex?.executions) ? (ex!.executions as Record<string, unknown>[]) : []
})

const fitnessScore = computed(() => Number((fitness.value?.data as Record<string, unknown> | undefined)?.score ?? 0))
const promotedCount = computed(() => Number((governance.value?.data as Record<string, unknown> | undefined)?.promoted ?? 0))
const runtimeCount = computed(() => {
  const d = deploy.value?.data as Record<string, unknown> | undefined
  return Array.isArray(d?.data) ? (d!.data as Record<string, unknown>[]).length : 0
})
const runtimeRows = computed(() => {
  const d = deploy.value?.data as Record<string, unknown> | undefined
  return Array.isArray(d?.data) ? (d!.data as Record<string, unknown>[]) : []
})
const recentFailures = computed(() => executions.value.filter((ex) => ['failed', 'cancelled'].includes(String(ex.status ?? ''))).slice(0, 5))
const contractStage = computed(() => String(lifecycleContract.value?.data?.stage ?? lifecycleContract.value?.stage ?? '—'))
const contractStatus = computed(() => String(lifecycleContract.value?.data?.status ?? lifecycleContract.value?.status ?? '—'))
const contractScore = computed(() => Number((lifecycleContract.value?.data as Record<string, unknown> | undefined)?.completion_score ?? 0))

function openTraceFromExecution(executionId: string) {
  router.push({ name: 'trace' })
  // 尝试将目标 execution 传给 trace/fix 联动层
  window.dispatchEvent(new CustomEvent('sprintcycle:focus-execution', { detail: { executionId } }))
}

function openFixFromRuntime(runtimeId: string) {
  router.push({ name: 'fix' })
  window.dispatchEvent(new CustomEvent('sprintcycle:focus-runtime', { detail: { runtimeId } }))
}

const topLinks = [
  { label: 'Trace', route: 'trace' },
  { label: 'Fix', route: 'fix' },
  { label: 'Promotion', route: 'promotion' },
  { label: 'Deploy', route: 'deploy' },
  { label: 'Fitness', route: 'fitness' },
]
</script>

<template>
  <div class="overview-page">
    <div class="hero">
      <div>
        <div class="eyebrow">SprintCycle ODD Factory</div>
        <h1>进化工厂总览</h1>
        <p class="subtitle">一页收口执行、观测、治理、修复、部署与评分。</p>
      </div>
      <el-button :loading="loading" type="primary" @click="refresh">刷新</el-button>
    </div>

    <el-row :gutter="16" class="mb">
      <el-col v-for="link in topLinks" :key="link.route" :xs="12" :md="4">
        <el-card shadow="never" class="nav-card" @click="router.push({ name: link.route })">
          <div class="nav-title">{{ link.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="panel-card">
          <template #header>执行记录</template>
          <el-table :data="executions" size="small" stripe>
            <el-table-column prop="execution_id" label="Execution ID" width="140" />
            <el-table-column prop="status" label="Status" width="100" />
            <el-table-column prop="release_plan_name" label="Plan" />
            <el-table-column prop="updated_at" label="Updated" width="180" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="panel-card">
          <template #header>关键摘要</template>
          <div class="summary-grid">
            <div><span>项目路径</span><b>{{ String(summary?.project_path ?? '') }}</b></div>
            <div><span>执行总数</span><b>{{ executions.length }}</b></div>
            <div><span>Fitness</span><b>{{ fitnessScore }}</b></div>
            <div><span>Promoted</span><b>{{ promotedCount }}</b></div>
            <div><span>Runtimes</span><b>{{ runtimeCount }}</b></div>
            <div><span>HITL</span><b>{{ String((summary?.hitl as Record<string, unknown> | undefined)?.open_requests ?? 0) }}</b></div>
          </div>
        </el-card>

        <el-card shadow="never" class="panel-card">
          <template #header>Lifecycle Contract</template>
          <div class="summary-grid">
            <div><span>Stage</span><b>{{ contractStage }}</b></div>
            <div><span>Status</span><b>{{ contractStatus }}</b></div>
            <div><span>Score</span><b>{{ contractScore }}</b></div>
            <div><span>Execution</span><b>{{ String(lifecycleContract?.data?.execution_id ?? lifecycleContract?.execution_id ?? '—') }}</b></div>
          </div>
        </el-card>

        <el-card shadow="never" class="panel-card risk-card">
          <template #header>风险区</template>
          <div v-if="recentFailures.length === 0" class="risk-empty">近期无失败执行</div>
          <div v-else class="risk-list">
            <div v-for="item in recentFailures" :key="String(item.execution_id ?? '')" class="risk-item" @click="openTraceFromExecution(String(item.execution_id ?? ''))">
              <div class="risk-title">{{ String(item.execution_id ?? '') }}</div>
              <div class="risk-meta">{{ String(item.status ?? '') }} · {{ String(item.error ?? '—') }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="panel-card">
          <template #header>最近运行</template>
          <div v-if="runtimeRows.length === 0" class="risk-empty">暂无 runtime</div>
          <div v-else class="runtime-list">
            <div v-for="item in runtimeRows.slice(0, 5)" :key="String(item.runtime_id ?? '')" class="runtime-item" @click="openFixFromRuntime(String(item.runtime_id ?? ''))">
              <div class="risk-title">{{ String(item.project_name ?? '') }}</div>
              <div class="risk-meta">{{ String(item.status ?? '') }} · {{ String(item.runtime_id ?? '') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
