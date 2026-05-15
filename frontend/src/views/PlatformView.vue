<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { apiConsoleOverview, apiDashboardLifecycleContract, apiExecutionDetail, apiExecutionReplay, apiPlatformSummary, apiRollback, apiRun } from '@/api'

type Summary = Record<string, unknown>

const loading = ref(false)
const error = ref('')
const summary = ref<Summary | null>(null)
const consoleOverview = ref<Summary | null>(null)
const replay = ref<Summary | null>(null)
const replayExecId = ref('')
const execDetail = ref<Summary | null>(null)
const lifecycleContract = ref<Summary | null>(null)
const selectedExecId = ref('')
const pollMs = 4000
let timer: ReturnType<typeof setInterval> | null = null

function fmtUptime(sec: unknown): string {
  const s = typeof sec === 'number' ? sec : 0
  if (s < 60) return `${Math.round(s)}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ${Math.round(s % 60)}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

function asNum(v: unknown): number {
  return typeof v === 'number' ? v : 0
}

function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === 'object' ? (v as Record<string, unknown>) : {}
}

function asList(v: unknown): Record<string, unknown>[] {
  return Array.isArray(v) ? (v as Record<string, unknown>[]) : []
}

function fmtAuditTs(ts: unknown): string {
  const t = typeof ts === 'number' ? ts : 0
  if (!t) return ''
  return new Date(t * 1000).toLocaleTimeString('zh-CN', { hour12: false })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    summary.value = await apiPlatformSummary()
    consoleOverview.value = await apiConsoleOverview(20)
    const primary = asRecord(asRecord(summary.value?.executions_overview).primary_execution)
    const execId = selectedExecId.value || (typeof primary.execution_id === 'string' ? primary.execution_id : '')
    selectedExecId.value = execId
    replayExecId.value = execId
    replay.value = execId ? await apiExecutionReplay(execId, 200) : null
    execDetail.value = execId ? await apiExecutionDetail(execId, 120) : null
    lifecycleContract.value = execId ? await apiDashboardLifecycleContract(execId, 120) : null
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    summary.value = null
    consoleOverview.value = null
    replay.value = null
    execDetail.value = null
    lifecycleContract.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
  timer = setInterval(() => void load(), pollMs)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  timer = null
})

function eventBars(s: Summary | null): { key: string; n: number; pct: number }[] {
  const obs = asRecord(s?.execution_events_observed)
  const entries = Object.entries(obs)
    .map(([key, n]) => ({ key, n: asNum(n) }))
    .filter((x) => x.n > 0)
    .sort((a, b) => b.n - a.n)
  const max = entries.reduce((m, x) => Math.max(m, x.n), 1)
  return entries.slice(0, 12).map((x) => ({ ...x, pct: Math.round((100 * x.n) / max) }))
}

const primaryLine = computed(() => {
  const s = summary.value
  if (!s) return '—'
  const p = asRecord(asRecord(s.executions_overview).primary_execution)
  const zh = p.lane_label_zh
  if (!zh) return '无活跃执行'
  const id = typeof p.execution_id === 'string' ? p.execution_id.slice(0, 10) : ''
  return id ? `${zh} · ${id}` : String(zh)
})

const consoleRuns = computed(() => asList(asRecord(consoleOverview.value?.data ?? consoleOverview.value).executions))
const recoverableRuns = computed(() => asList(asRecord(consoleOverview.value?.data ?? consoleOverview.value).recoverable_executions))
const replaySummary = computed(() => asRecord(replay.value?.data ?? replay.value))
const replayTimeline = computed(() => asList(replay.value?.timeline))
const detailState = computed(() => asRecord(execDetail.value?.data ?? execDetail.value).state)
const detailCheckpoint = computed(() => asRecord(execDetail.value?.data ?? execDetail.value).checkpoint)
const detailResume = computed(() => asRecord(execDetail.value?.data ?? execDetail.value).resume_point)
const detailCanResume = computed(() => Boolean((execDetail.value?.data ?? (execDetail.value as Record<string, unknown>))?.can_resume))
const contractData = computed(() => asRecord(lifecycleContract.value?.data ?? lifecycleContract.value))
const contractScore = computed(() => Number(contractData.value.completion_score ?? 0))
const contractStage = computed(() => String(contractData.value.stage ?? '—'))
const contractStatus = computed(() => String(contractData.value.status ?? '—'))
const failureHint = computed(() => {
  const d = asRecord(execDetail.value?.data ?? execDetail.value)
  const st = String(asRecord(d.state).status ?? '')
  if (!d.state || st === 'success' || st === 'completed') return '当前执行未进入失败态'
  if (detailCanResume.value) return '建议优先续跑；若状态游标不可靠，可先查看 checkpoint 后再回放。'
  return '建议先查看 checkpoint 与最后稳定态；必要时执行回滚后重新规划。'
})

async function selectExecution(execId: string) {
  if (!execId) return
  selectedExecId.value = execId
  replayExecId.value = execId
  replay.value = await apiExecutionReplay(execId, 200)
  execDetail.value = await apiExecutionDetail(execId, 120)
}

async function resumeSelectedExecution() {
  if (!selectedExecId.value) return
  loading.value = true
  try {
    await apiRun({ execution_id: selectedExecId.value, resume: true })
    await load()
  } finally {
    loading.value = false
  }
}

async function rollbackSelectedExecution() {
  if (!selectedExecId.value) return
  loading.value = true
  try {
    await apiRollback(selectedExecId.value)
    await load()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="platform">
    <div class="platform-head">
      <div>
        <h1 class="title">运行总览</h1>
        <p class="sub">
          HTTP / SSE 指标、执行阶段、人机待办 — 控制台进程内聚合（随服务重启清零）
        </p>
      </div>
      <el-button :loading="loading" type="primary" @click="load">刷新</el-button>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon class="mb" />

    <template v-if="summary">
      <el-row :gutter="16" class="mb">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">项目路径</div>
            <div class="metric-value mono small">{{ String(summary.project_path ?? '') }}</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">进程运行时间</div>
            <div class="metric-value">
              {{ fmtUptime(asRecord(summary.process).uptime_seconds) }}
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">SSE 连接 / HITL 待办</div>
            <div class="metric-value">
              {{ asNum(asRecord(summary.sse).connected_clients) }}
              <span class="sep">·</span>
              {{ asNum(asRecord(summary.hitl).open_requests) }}
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">HTTP 请求 / 错误</div>
            <div class="metric-value">
              {{ asNum(asRecord(summary.http).requests_total) }}
              <span class="sep">·</span>
              <span :class="{ warn: asNum(asRecord(summary.http).requests_4xx_5xx) > 0 }">
                {{ asNum(asRecord(summary.http).requests_4xx_5xx) }}
              </span>
            </div>
            <div class="metric-foot">
              平均 {{ asNum(asRecord(summary.http).avg_duration_ms) }} ms · status()
              {{ asNum(summary.status_query_ms) }} ms
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="14">
          <el-card shadow="never" class="sc-card">
            <template #header>
              <span>执行会话与 Sprint 阶段</span>
              <span class="hint">主关注：{{ primaryLine }}</span>
            </template>
            <div class="chips mb">
              <span
                v-for="(n, st) in asRecord(asRecord(summary.executions_overview).by_status)"
                :key="String(st)"
                class="chip"
              >
                {{ st }}: <b>{{ n }}</b>
              </span>
              <span v-if="!Object.keys(asRecord(asRecord(summary.executions_overview).by_status)).length" class="muted">
                暂无执行记录
              </span>
            </div>
            <el-table
              :data="asList(asRecord(summary.executions_overview).executions)"
              size="small"
              stripe
              max-height="360"
            >
              <el-table-column prop="execution_id" label="执行 ID" width="120">
                <template #default="{ row }">
                  <span class="mono clickable" @click="selectExecution(String(row.execution_id ?? ''))">{{ String(row.execution_id ?? '').slice(0, 10) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="release_plan_name" label="计划" min-width="100" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column label="阶段（控制台）" min-width="160">
                <template #default="{ row }">
                  <div>{{ row.lane_label_zh }}</div>
                  <div v-if="row.lane_hint" class="muted tiny">{{ row.lane_hint }}</div>
                </template>
              </el-table-column>
              <el-table-column label="进度" width="120">
                <template #default="{ row }">
                  <el-progress
                    v-if="row.progress_percent != null"
                    :percentage="Number(row.progress_percent)"
                    :stroke-width="6"
                    :show-text="true"
                  />
                  <span v-else class="muted">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="updated_at" label="更新" width="160" />
            </el-table>
            <div class="chips mb" style="margin-top: 12px;">
              <span class="chip">已选执行: <b>{{ selectedExecId ? selectedExecId.slice(0, 10) : 'primary' }}</b></span>
              <el-button size="small" @click="selectExecution(String(asList(asRecord(summary.executions_overview).executions)[0]?.execution_id ?? ''))">切换到首条执行</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="10">
          <el-card shadow="never" class="sc-card mb">
            <template #header>执行事件类型（本进程观测）</template>
            <div v-if="!eventBars(summary).length" class="muted">尚无事件</div>
            <div v-for="b in eventBars(summary)" :key="b.key" class="bar-row">
              <span class="bar-name mono">{{ b.key }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: b.pct + '%' }" />
              </div>
              <span class="bar-n">{{ b.n }}</span>
            </div>
          </el-card>
          <el-card shadow="never" class="sc-card mb">
            <template #header>控制台总览</template>
            <div class="chips mb">
              <span v-if="consoleRuns.length" class="chip">可观测执行: <b>{{ consoleRuns.length }}</b></span>
              <span v-if="recoverableRuns.length" class="chip">可恢复: <b>{{ recoverableRuns.length }}</b></span>
              <span v-if="replaySummary.execution_id" class="chip">回放: <b>{{ replayExecId.slice(0, 10) }}</b></span>
              <span v-if="detailCanResume" class="chip ok">可续跑</span>
            </div>
            <div class="chips mb">
              <el-button size="small" @click="selectExecution(replayExecId)">刷新当前执行</el-button>
              <el-button size="small" type="primary" :disabled="!detailCanResume" @click="resumeSelectedExecution">续跑</el-button>
              <el-button size="small" type="warning" :disabled="!selectedExecId" @click="rollbackSelectedExecution">回滚</el-button>
            </div>
            <div class="detail-box">
              <div class="detail-row mono"><span>失败建议</span><b>{{ failureHint }}</b></div>
            </div>
            <div class="timeline">
              <div v-if="replaySummary.execution_id" class="muted tiny mb">
                {{ replaySummary.execution_id }} · {{ replaySummary.status }} · last stable: {{ JSON.stringify(replaySummary.last_stable_state ?? {}) }}
              </div>
              <div v-if="detailState.execution_id" class="detail-box">
                <div class="detail-row mono"><span>状态</span><b>{{ String(detailState.status ?? '') }}</b></div>
                <div class="detail-row mono"><span>当前 Sprint</span><b>{{ String(detailState.current_sprint ?? '') }}/{{ String(detailState.total_sprints ?? '') }}</b></div>
                <div class="detail-row mono"><span>Checkpoint</span><b>{{ String(detailCheckpoint.sprint_name ?? '') }}</b></div>
                <div class="detail-row mono"><span>Resume</span><b>{{ String(detailResume.sprint_name ?? '') }}</b></div>
              </div>
              <div v-for="(ev, idx) in replayTimeline.slice(-10)" :key="idx" class="timeline-line mono">
                <span class="muted">{{ String(ev.timestamp ?? ev.created_at ?? '') }}</span>
                <span>{{ String(ev.event_type ?? '') }}</span>
                <span class="muted">{{ String(ev.data?.description ?? ev.data?.message ?? '') }}</span>
              </div>
              <div v-if="!replayTimeline.length" class="muted">暂无可回放事件</div>
            </div>
          </el-card>
          <el-card shadow="never" class="sc-card">
            <template #header>最近 API 审计</template>
            <div class="audit">
              <div
                v-for="(a, idx) in asList(summary.recent_activity).slice().reverse()"
                :key="idx"
                class="audit-line mono"
              >
                <span class="muted">{{ fmtAuditTs(a.ts) }}</span>
                {{ a.method }} {{ a.route }}
                <span :class="asNum(a.status_code) >= 400 ? 'bad' : 'ok'">{{ a.status_code }}</span>
                {{ a.duration_ms }}ms
              </div>
            </div>
          </el-card>

          <el-card shadow="never" class="sc-card" style="margin-top: 16px;">
            <template #header>Lifecycle Contract</template>
            <div class="detail-box">
              <div class="detail-row mono"><span>Stage</span><b>{{ contractStage }}</b></div>
              <div class="detail-row mono"><span>Status</span><b>{{ contractStatus }}</b></div>
              <div class="detail-row mono"><span>Score</span><b>{{ contractScore }}</b></div>
              <div class="detail-row mono"><span>Execution</span><b>{{ String(contractData.execution_id ?? selectedExecId ?? '') }}</b></div>
              <div class="detail-row mono"><span>Promotion Ready</span><b>{{ String(Boolean(contractData.promotion?.passed ?? false)) }}</b></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style scoped>
.platform {
  max-width: 1280px;
  margin: 0 auto;
}
.platform-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}
.title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
}
.sub {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  max-width: 640px;
}
.mb {
  margin-bottom: 16px;
}
.metric-card {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
  margin-bottom: 16px;
}
.metric-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}
.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}
.metric-value.small {
  font-size: 13px;
  font-weight: 500;
  word-break: break-all;
}
.metric-foot {
  margin-top: 8px;
  font-size: 11px;
  color: #64748b;
}
.sep {
  color: #64748b;
  margin: 0 6px;
}
.warn {
  color: #f97316;
}
.sc-card {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
  color: #e2e8f0;
}
.hint {
  float: right;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #0f172a;
  border: 1px solid #334155;
  color: #cbd5e1;
}
.muted {
  color: #64748b;
}
.tiny {
  font-size: 11px;
}
.mono {
  font-family: ui-monospace, monospace;
}
.clickable {
  cursor: pointer;
  text-decoration: underline;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}
.bar-name {
  width: 140px;
  flex-shrink: 0;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bar-track {
  flex: 1;
  height: 8px;
  background: #0f172a;
  border-radius: 4px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8);
  border-radius: 4px;
}
.bar-n {
  width: 36px;
  text-align: right;
  color: #e2e8f0;
}
.audit {
  max-height: 280px;
  overflow-y: auto;
  font-size: 11px;
}
.audit-line {
  padding: 4px 0;
  border-bottom: 1px solid #334155;
  color: #cbd5e1;
}
.audit-line .ok {
  color: #22c55e;
}
.audit-line .bad {
  color: #f87171;
}
.timeline {
  max-height: 320px;
  overflow-y: auto;
}
.timeline-line {
  padding: 6px 0;
  border-bottom: 1px solid #334155;
  color: #cbd5e1;
  font-size: 11px;
  display: grid;
  grid-template-columns: 180px 140px 1fr;
  gap: 8px;
}
.detail-box {
  margin: 8px 0 12px;
  padding: 10px 12px;
  border: 1px solid #334155;
  border-radius: 10px;
  background: #0f172a;
}
.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  color: #e2e8f0;
}
</style>
