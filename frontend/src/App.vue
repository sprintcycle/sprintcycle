<script setup lang="ts">
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import { apiClients, apiDiagnose, apiPlan, apiRun, apiStatus, apiStop, looksLikeYaml } from './api'
import { connectSSE, disconnectSSE, subscribeSSE } from './sse'

type EventLine = { type: string; ts: string; display: string; text: string; agent?: string }

const TAB_PLAN = 'plan'
const TAB_HISTORY = 'history'
const TAB_DIAG = 'diag'
const TAB_EVENTS = 'events'

const activeTab = ref(TAB_PLAN)
const yamlInput = ref('')
const planBusy = ref(false)
const planMeta = ref('')
const planMessage = ref('点击 **Plan** 预览执行计划，或直接 **Run** 开始执行')
const planTone = ref<'muted' | 'loading' | 'error' | 'ok'>('muted')

const executions = ref<Record<string, unknown>[]>([])
const historyLoaded = ref(false)
const expanded = ref<Record<string, boolean>>({})

const diagnoseLoading = ref(false)
const diagnoseScore = ref<number | null>(null)
const diagnoseTitle = ref('项目诊断')
const diagnoseDesc = ref('点击下方按钮检查项目健康状态')
const diagnoseIssues = ref<Record<string, unknown>[]>([])
const diagnoseStats = ref({ pass: 0, warn: 0, fail: 0 })

const sseLabel = ref('disconnected')
const sseDotClass = ref<'off' | 'ok' | 'bad'>('off')
const clientCount = ref(0)
const liveEventCount = ref(0)
const eventLines = ref<EventLine[]>([])
const autoScrollEvents = ref(true)
const eventsLogRef = ref<HTMLElement | null>(null)

let unsubSSE: (() => void) | null = null
let pollClients: ReturnType<typeof setInterval> | null = null

const historyBadge = computed(() => executions.value.length)

const EVENT_META: Record<string, { icon: string; label: string }> = {
  execution_start: { icon: '🚀', label: 'EXEC START' },
  sprint_start: { icon: '📦', label: 'SPRINT START' },
  sprint_complete: { icon: '✅', label: 'SPRINT DONE' },
  sprint_failed: { icon: '❌', label: 'SPRINT FAIL' },
  task_start: { icon: '📋', label: 'TASK START' },
  task_complete: { icon: '✅', label: 'TASK DONE' },
  task_failed: { icon: '❌', label: 'TASK FAIL' },
  governance_task_check: { icon: '🛡', label: 'GOV TASK' },
  governance_gate: { icon: '📐', label: 'GOV GATE' },
  execution_complete: { icon: '🎉', label: 'EXEC DONE' },
  execution_failed: { icon: '💥', label: 'EXEC FAIL' },
  evolution_candidate: { icon: '🧬', label: 'EVOLUTION' },
  heartbeat: { icon: '💓', label: 'HEARTBEAT' },
  ping: { icon: '📶', label: 'PING' },
}

function buildEventLine(data: Record<string, unknown>): string {
  const parts: string[] = []
  const exId = data.execution_id
  if (typeof exId === 'string') parts.push(`[${exId.slice(0, 8)}]`)
  if (typeof data.sprint_name === 'string') parts.push(data.sprint_name)
  if (typeof data.gate === 'string') parts.push(`gate:${data.gate}`)
  const cr = data.compose_rule_ids
  if (Array.isArray(cr) && cr.length) parts.push(`compose: ${cr.join(', ')}`)
  const hits = data.compose_hits
  if (Array.isArray(hits)) {
    hits.slice(0, 2).forEach((h) => {
      if (h && typeof h === 'object') {
        const o = h as Record<string, unknown>
        parts.push(`${String(o.rule_id ?? '')}: ${String(o.message ?? '').slice(0, 100)}`)
      }
    })
  }
  if (data.error_count !== undefined || data.warning_count !== undefined) {
    parts.push(`err ${data.error_count ?? 0} / warn ${data.warning_count ?? 0}`)
  }
  if (typeof data.check_id === 'string' || typeof data.check_id === 'number') parts.push(`#${data.check_id}`)
  if (typeof data.description === 'string') parts.push(data.description)
  if (typeof data.agent_type === 'string') parts.push(`@${data.agent_type}`)
  if (typeof data.error === 'string') parts.push(`⚠ ${data.error}`)
  if (typeof data.duration === 'number') parts.push(`${data.duration.toFixed(1)}s`)
  if (typeof data.message === 'string' && parts.length === 0) return data.message
  return parts.join(' · ')
}

async function refreshClients() {
  try {
    const d = await apiClients()
    clientCount.value = d.client_count ?? 0
  } catch {
    /* ignore */
  }
}

function pushEvent(type: string, data: Record<string, unknown>) {
  const meta = EVENT_META[type] ?? { icon: '?', label: type.toUpperCase() }
  const tsRaw = data.timestamp
  const ts =
    typeof tsRaw === 'number' || typeof tsRaw === 'string'
      ? new Date(tsRaw).toLocaleTimeString('zh-CN', { hour12: false })
      : ''
  const agent =
    typeof data.agent_type === 'string' ? data.agent_type : undefined
  eventLines.value.push({
    type,
    ts,
    display: `${meta.icon} ${meta.label}`,
    text: buildEventLine(data),
    agent,
  })
  liveEventCount.value += 1
}

watch(
  eventLines,
  async () => {
    await nextTick()
    const el = eventsLogRef.value
    if (el && autoScrollEvents.value) el.scrollTop = el.scrollHeight
  },
  { deep: true },
)

function wireSSE() {
  unsubSSE = subscribeSSE((type, data) => {
    if (type === '_open') {
      sseLabel.value = 'connected'
      sseDotClass.value = 'ok'
      void refreshClients()
      return
    }
    if (type === '_close') {
      sseLabel.value = 'reconnecting...'
      sseDotClass.value = 'bad'
      return
    }
    if (type === '_error') {
      sseLabel.value = 'disconnected'
      sseDotClass.value = 'bad'
      return
    }
    pushEvent(type, data)
  })
  connectSSE()
}

function fmtErr(e: unknown): string {
  if (axios.isAxiosError(e)) return e.message || '请求失败'
  if (e instanceof Error) return e.message
  return String(e)
}

function planPayload() {
  const input = yamlInput.value.trim()
  const body = looksLikeYaml(input) ? { release_plan_yaml: input } : { intent: input }
  return { input, body }
}

async function handlePlan() {
  const { input, body } = planPayload()
  if (!input) {
    ElMessage.warning('请输入执行计划 YAML 或意图描述')
    return
  }
  planBusy.value = true
  planTone.value = 'loading'
  planMessage.value = '⏳ 正在规划...'
  planMeta.value = ''
  try {
    const data = await apiPlan(body)
    if (data.success === false && typeof data.error === 'string') {
      planTone.value = 'error'
      planMessage.value = `❌ ${data.error}`
      return
    }
    renderPlanIntoMessage(data)
  } catch (e) {
    planTone.value = 'error'
    planMessage.value = `请求失败：${fmtErr(e)}`
  } finally {
    planBusy.value = false
  }
}

async function handleRun() {
  const { input, body } = planPayload()
  if (!input) {
    ElMessage.warning('请输入执行计划 YAML 或意图描述')
    return
  }
  planBusy.value = true
  planTone.value = 'loading'
  planMessage.value = '🚀 正在执行... 请关注「实时事件」页'
  planMeta.value = ''
  try {
    const data = await apiRun(body)
    renderPlanIntoMessage(data)
    await loadHistory()
  } catch (e) {
    planTone.value = 'error'
    planMessage.value = `请求失败：${fmtErr(e)}`
  } finally {
    planBusy.value = false
  }
}

function renderPlanIntoMessage(data: Record<string, unknown>) {
  if (data.success === false && typeof data.error === 'string') {
    planTone.value = 'error'
    planMessage.value = `❌ ${data.error}`
    return
  }
  const sprints = data.sprints
  if (!Array.isArray(sprints) || sprints.length === 0) {
    planTone.value = 'ok'
    planMessage.value = '✅ 计划为空'
    return
  }
  const metaParts: string[] = []
  if (typeof data.release_plan_name === 'string') metaParts.push(`📦 ${data.release_plan_name}`)
  if (typeof data.mode === 'string') metaParts.push(`⚙ ${data.mode}`)
  metaParts.push(`📦 ${sprints.length} Sprint`)
  if (typeof data.duration === 'number') metaParts.push(`⏱ ${data.duration.toFixed(2)}s`)
  planMeta.value = metaParts.join(' · ')

  const lines: string[] = [`📋 执行计划预览`]
  lines.push('')
  let i = 0
  for (const sp of sprints) {
    i += 1
    if (!sp || typeof sp !== 'object') continue
    const s = sp as Record<string, unknown>
    const name = typeof s.name === 'string' ? s.name : 'Unnamed'
    lines.push(`Sprint ${i}: ${name}`)
    const tasks = s.tasks
    if (Array.isArray(tasks)) {
      for (const t of tasks) lines.push(typeof t === 'string' ? `  → ${t}` : `  → ${JSON.stringify(t)}`)
    }
    lines.push('')
  }
  planTone.value = 'ok'
  planMessage.value = lines.join('\n')
}

function clearEditor() {
  yamlInput.value = ''
  planMeta.value = ''
  planTone.value = 'muted'
  planMessage.value = '已清空，点击 **Plan** 预览执行计划'
}

async function loadHistory() {
  try {
    const data = await apiStatus()
    if (data.success === false) {
      ElMessage.error(String(data.error ?? '加载失败'))
      return
    }
    const list = data.executions
    executions.value = Array.isArray(list) ? (list as Record<string, unknown>[]) : []
    historyLoaded.value = true
  } catch (e) {
    ElMessage.error(fmtErr(e))
  }
}

function toggleExpand(id: string) {
  expanded.value = { ...expanded.value, [id]: !expanded.value[id] }
}

function sprintRows(ex: Record<string, unknown>) {
  const meta = ex.metadata as Record<string, unknown> | undefined
  const cp = ex.checkpoint as Record<string, unknown> | undefined
  const fromMeta = meta?.sprint_history
  const fromCp = cp?.sprint_history
  const raw = Array.isArray(fromMeta) ? fromMeta : Array.isArray(fromCp) ? fromCp : []
  return raw as Record<string, unknown>[]
}

function taskRows(sp: Record<string, unknown>): unknown[] {
  const tr = sp.task_results
  const ts = sp.tasks
  if (Array.isArray(tr)) return tr
  if (Array.isArray(ts)) return ts
  return []
}

function shortId(id: string) {
  return id.length > 8 ? id.slice(0, 8) : id
}

function canResume(ex: Record<string, unknown>): boolean {
  const st = String(ex.status ?? '')
  const chk = ex.checkpoint
  return ['cancelled', 'failed', 'paused'].includes(st) && Boolean(chk)
}

async function handleStop(execId: string) {
  try {
    await ElMessageBox.confirm(`确认停止执行 ${shortId(execId)} ?`, '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await apiStop(execId)
    await loadHistory()
  } catch (e) {
    ElMessage.error(fmtErr(e))
  }
}

async function handleResume(execId: string) {
  try {
    await ElMessageBox.confirm(`确认恢复执行 ${shortId(execId)} ?`, '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    const data = await apiRun({ execution_id: execId, resume: true })
    if (data.success === false) {
      ElMessage.error(String(data.error ?? 'Resume 失败'))
      return
    }
    activeTab.value = TAB_EVENTS
    await loadHistory()
  } catch (e) {
    ElMessage.error(fmtErr(e))
  }
}

async function runDiagnose() {
  diagnoseLoading.value = true
  try {
    const data = await apiDiagnose()
    if (data.success === false && typeof data.error === 'string') {
      diagnoseDesc.value = `诊断失败：${data.error}`
      return
    }
    const score = typeof data.health_score === 'number' ? data.health_score : 0
    diagnoseScore.value = Math.round(score)
    const issues = Array.isArray(data.issues) ? (data.issues as Record<string, unknown>[]) : []
    diagnoseIssues.value = issues
    let pass = 0
    let warn = 0
    let fail = 0
    for (const i of issues) {
      const sev = String(i.severity ?? 'info').toLowerCase()
      if (['pass', 'ok', 'info'].includes(sev)) pass += 1
      else if (['warn', 'warning'].includes(sev)) warn += 1
      else if (['fail', 'error', 'critical'].includes(sev)) fail += 1
    }
    diagnoseStats.value = { pass, warn, fail }
    if (score >= 80) {
      diagnoseTitle.value = '✅ 项目健康'
      diagnoseDesc.value = `健康分 ${diagnoseScore.value}/100，共 ${issues.length} 项检查`
    } else if (score >= 50) {
      diagnoseTitle.value = '⚠ 项目需要注意'
      diagnoseDesc.value = `健康分 ${diagnoseScore.value}/100，失败 ${fail} / 警告 ${warn}`
    } else {
      diagnoseTitle.value = '🚨 项目需要修复'
      diagnoseDesc.value = `健康分 ${diagnoseScore.value}/100，存在 ${fail} 个关键问题`
    }
  } catch (e) {
    diagnoseDesc.value = `诊断请求失败：${fmtErr(e)}`
  } finally {
    diagnoseLoading.value = false
  }
}

function clearEvents() {
  eventLines.value = []
  liveEventCount.value = 0
}

watch(activeTab, (t) => {
  if (t === TAB_HISTORY) void loadHistory()
})

function scoreColor(score: number) {
  if (score >= 80) return '#22c55e'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

function issueIcon(sev: string) {
  if (['pass', 'ok'].includes(sev)) return '✅'
  if (['warn', 'warning'].includes(sev)) return '⚠️'
  if (['fail', 'error', 'critical'].includes(sev)) return '❌'
  return 'ℹ️'
}

onMounted(() => {
  document.documentElement.classList.add('dark')
  wireSSE()
  pollClients = setInterval(refreshClients, 5000)
  void refreshClients()
  void loadHistory()
})

onUnmounted(() => {
  disconnectSSE({ keepListeners: false })
  unsubSSE?.()
  if (pollClients) clearInterval(pollClients)
})
</script>

<template>
  <div class="sc-app">
      <header class="sc-header">
        <div class="sc-logo">
          🚀 SprintCycle <span class="sc-logo-sub">Dashboard</span>
        </div>
        <div class="sc-header-right">
          <span class="sc-pill">
            <span class="dot" :class="sseDotClass" />
            <span>{{ sseLabel }}</span>
          </span>
          <span class="sc-pill">Clients: <b>{{ clientCount }}</b></span>
          <span class="sc-pill">Events: <b>{{ liveEventCount }}</b></span>
        </div>
      </header>

      <el-tabs v-model="activeTab" class="sc-tabs">
        <el-tab-pane :label="'📝 执行计划'" :name="TAB_PLAN">
          <el-row :gutter="16" class="sc-plan-grid">
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="sc-card">
                <template #header>
                  📝 执行计划 YAML
                  <span class="sc-hint">支持自然语言或直接输入 YAML · Ctrl/Cmd+Enter 运行</span>
                </template>
                <el-input
                  v-model="yamlInput"
                  type="textarea"
                  :rows="18"
                  class="sc-yaml-input"
                  placeholder="输入 YAML 或自然语言意图..."
                  @keydown.ctrl.enter.prevent="handleRun"
                  @keydown.meta.enter.prevent="handleRun"
                />
                <div class="sc-card-actions">
                  <el-button @click="clearEditor">🗑️ 清空</el-button>
                  <div class="grow" />
                  <el-button :loading="planBusy" @click="handlePlan">📋 Plan</el-button>
                  <el-button type="success" :loading="planBusy" @click="handleRun">
                    ▶ Run
                  </el-button>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card shadow="never" class="sc-card">
                <template #header>
                  📊 计划预览 <span class="sc-hint">{{ planMeta }}</span>
                </template>
                <div
                  class="sc-plan-out"
                  :class="[`tone-${planTone}`]"
                >
                  <pre class="pre">{{ planMessage }}</pre>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane :name="TAB_HISTORY">
          <template #label>
            <span>📜 执行历史</span>
            <el-badge v-if="historyBadge > 0" :value="historyBadge" class="tab-badge" />
          </template>
          <div class="sc-history">
            <div class="sc-history-toolbar">
              <span class="sc-muted">近期执行记录</span>
              <el-button size="small" @click="loadHistory">🔄 刷新</el-button>
            </div>
            <div v-if="!historyLoaded" class="sc-muted">加载中...</div>
            <div v-else-if="executions.length === 0" class="sc-empty">
              📭 暂无执行历史
            </div>
            <div v-else class="exec-list">
              <el-card v-for="ex in executions" :key="String(ex.execution_id)" class="exec-card" shadow="hover">
                <div class="exec-row" @click="toggleExpand(String(ex.execution_id ?? ''))">
                  <span class="exec-short">{{ shortId(String(ex.execution_id ?? '')) }}</span>
                  <el-tag size="small" effect="dark">{{ String(ex.status ?? 'unknown') }}</el-tag>
                  <div class="exec-meta">
                    <span v-if="ex.release_plan_name">📦 {{ ex.release_plan_name }}</span>
                    <span v-if="ex.mode">⚙ {{ ex.mode }}</span>
                    <span v-if="Number(ex.total_sprints) > 0">
                      Sprint {{ ex.current_sprint ?? 0 }}/{{ ex.total_sprints }}
                    </span>
                    <span v-if="ex.completed_tasks != null">
                      📋 {{ ex.completed_tasks }}/{{ ex.total_tasks ?? '?' }} 任务
                    </span>
                    <span v-if="ex.created_at">🕐 {{ new Date(String(ex.created_at)).toLocaleString('zh-CN') }}</span>
                    <span v-if="ex.error" class="err">❌ {{ String(ex.error).slice(0, 80) }}</span>
                  </div>
                  <div class="exec-actions">
                    <el-button
                      v-if="canResume(ex)"
                      type="success"
                      size="small"
                      @click.stop="handleResume(String(ex.execution_id))"
                    >
                      ▶ Resume
                    </el-button>
                    <el-button size="small" @click.stop="handleStop(String(ex.execution_id))">⏹</el-button>
                  </div>
                  <span class="chev" :class="{ open: expanded[String(ex.execution_id)] }">▶</span>
                </div>
                <div v-show="expanded[String(ex.execution_id)]" class="exec-detail">
                  <div v-if="sprintRows(ex).length === 0" class="sc-muted pad">暂无详细信息</div>
                  <div v-else class="sprint-section">
                    <div v-for="(sp, si) in sprintRows(ex)" :key="si" class="sprint-card">
                      <div class="sprint-head">
                        <span class="sprint-dot" :class="String((sp as any).status ?? '')" />
                        <b>{{ String((sp as any).sprint_name ?? (sp as any).name ?? `Sprint ${si + 1}`) }}</b>
                        <span class="sc-muted">{{ String((sp as any).status ?? '') }}</span>
                        <span v-if="typeof (sp as any).duration === 'number'" class="sc-muted">
                          ⏱ {{ Number((sp as any).duration).toFixed(1) }}s
                        </span>
                      </div>
                      <div v-for="(t, ti) in taskRows(sp as Record<string, unknown>)" :key="ti" class="task-row">
                        <template v-if="typeof t === 'string'">
                          {{ t }}
                        </template>
                        <template v-else-if="t && typeof t === 'object'">
                          <span :class="'ic-' + String((t as any).status ?? '')">
                            {{ (t as any).status === 'failed' ? '❌' : (t as any).status === 'success' ? '✅' : '⏳' }}
                          </span>
                          <span>{{ String((t as any).description ?? '') }}</span>
                          <span class="sc-muted agent">{{ String((t as any).agent ?? '') }}</span>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="🏥 诊断" :name="TAB_DIAG">
          <div class="diag">
            <el-row :gutter="20" align="middle">
              <el-col :span="8" :xs="24">
                <div v-if="diagnoseScore != null" class="score-ring">
                  <el-progress type="dashboard" :percentage="diagnoseScore" :color="scoreColor(diagnoseScore)" />
                  <div class="score-num" :style="{ color: scoreColor(diagnoseScore) }">
                    {{ diagnoseScore }}
                  </div>
                  <div class="sc-muted">健康分</div>
                </div>
                <div v-else class="sc-muted">尚未诊断</div>
              </el-col>
              <el-col :span="16" :xs="24">
                <h2>{{ diagnoseTitle }}</h2>
                <p class="sc-muted">{{ diagnoseDesc }}</p>
                <el-button :loading="diagnoseLoading" type="primary" @click="runDiagnose">
                  🏥 开始诊断
                </el-button>
                <div v-if="diagnoseIssues.length" class="diag-counts">
                  <span class="ok">通过 {{ diagnoseStats.pass }}</span>
                  <span class="warn">警告 {{ diagnoseStats.warn }}</span>
                  <span class="fail">失败 {{ diagnoseStats.fail }}</span>
                </div>
              </el-col>
            </el-row>
            <h3 class="section-title">检查项</h3>
            <el-row :gutter="12">
              <el-col v-for="(issue, ii) in diagnoseIssues" :key="ii" :span="12" :xs="24">
                <el-card shadow="never" class="diag-item">
                  <div class="item-row">
                    <span class="item-ico">{{ issueIcon(String(issue.severity ?? 'info').toLowerCase()) }}</span>
                    <div>
                      <div class="item-sev">{{ String(issue.severity ?? 'INFO').toUpperCase() }}</div>
                      <div class="item-msg">{{ String(issue.message ?? issue.msg ?? JSON.stringify(issue)) }}</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <div v-if="diagnoseIssues.length === 0 && diagnoseScore != null" class="sc-muted">
              暂无详细检查项
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :name="TAB_EVENTS">
          <template #label>
            <span>📡 实时事件</span>
            <el-badge :value="liveEventCount" class="tab-badge" />
          </template>
          <div class="events-wrap">
            <div class="events-toolbar">
              <span class="sc-muted">实时事件流 (SSE)</span>
              <el-checkbox v-model="autoScrollEvents">自动滚动</el-checkbox>
              <el-button size="small" @click="clearEvents">🗑️ 清除</el-button>
            </div>
            <div ref="eventsLogRef" class="events-log">
              <div v-for="(row, ri) in eventLines" :key="ri" class="event-line" :class="'t-' + row.type">
                <span class="ev-ts">{{ row.ts }}</span>
                <span class="ev-type">{{ row.display }}</span>
                <span class="ev-msg">{{ row.text }}</span>
                <el-tag v-if="row.agent" size="small" type="info" effect="dark">{{ row.agent }}</el-tag>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
</template>

<style>
html.dark body {
  background: #0f172a;
  margin: 0;
}
</style>

<style scoped>
.sc-app {
  min-height: 100vh;
  background: #0f172a;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
}
.sc-header {
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 20px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}
.sc-logo {
  font-weight: 700;
  font-size: 18px;
  color: #38bdf8;
}
.sc-logo-sub {
  font-weight: 400;
  font-size: 13px;
  color: #94a3b8;
  margin-left: 8px;
}
.sc-header-right {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}
.sc-pill {
  font-size: 12px;
  color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 20px;
  padding: 4px 12px;
  background: #0f172a;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
}
.dot.ok {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}
.dot.bad {
  background: #ef4444;
}
.dot.off {
  background: #64748b;
}
.sc-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}
.sc-tabs :deep(.el-tabs__content) {
  padding: 16px;
}
.tab-badge {
  margin-left: 6px;
  vertical-align: middle;
}
.sc-plan-grid {
  align-items: stretch;
}
.sc-card {
  background: #1e293b;
  border: 1px solid #334155;
}
.sc-card :deep(.el-card__header) {
  color: #94a3b8;
  font-weight: 600;
  border-color: #334155;
}
.sc-hint {
  float: right;
  font-weight: 400;
  font-size: 11px;
  color: #64748b;
}
.sc-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}
.grow {
  flex: 1;
}
.sc-yaml-input :deep(.el-textarea__inner) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
  background: #0b1120;
  color: #e2e8f0;
}
.sc-plan-out {
  min-height: 360px;
  background: #0b1120;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #334155;
}
.sc-plan-out .pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.tone-muted .pre {
  color: #64748b;
  text-align: center;
}
.tone-loading .pre {
  color: #94a3b8;
  font-style: italic;
}
.tone-error .pre {
  color: #f87171;
}
.tone-ok .pre {
  color: #e2e8f0;
}
.sc-history-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}
.sc-muted {
  color: #94a3b8;
  font-size: 13px;
}
.sc-empty {
  text-align: center;
  padding: 48px;
  color: #64748b;
}
.exec-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.exec-card {
  background: #1e293b;
  border: 1px solid #334155;
}
.exec-row {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}
.exec-short {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: #818cf8;
}
.exec-meta {
  flex: 1;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #94a3b8;
}
.exec-meta .err {
  color: #f87171;
}
.exec-actions {
  display: flex;
  gap: 6px;
}
.chev {
  color: #64748b;
  transition: transform 0.2s;
}
.chev.open {
  transform: rotate(90deg);
}
.exec-detail {
  padding-top: 12px;
  border-top: 1px solid #334155;
}
.pad {
  padding: 14px 0;
}
.sprint-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sprint-card {
  background: #0b1120;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px;
}
.sprint-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.sprint-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
}
.sprint-dot.failed {
  background: #ef4444;
}
.sprint-dot.running {
  background: #60a5fa;
}
.sprint-dot.skipped {
  background: #f59e0b;
}
.task-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #94a3b8;
  padding: 4px 0;
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
}
.task-row:last-child {
  border-bottom: none;
}
.agent {
  margin-left: auto;
}
.diag .score-ring {
  text-align: center;
}
.score-num {
  font-size: 22px;
  font-weight: 700;
}
.section-title {
  margin-top: 24px;
  font-size: 13px;
  color: #94a3b8;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.diag-counts {
  margin-top: 12px;
  display: flex;
  gap: 16px;
  font-size: 13px;
}
.diag-counts .ok {
  color: #4ade80;
}
.diag-counts .warn {
  color: #fbbf24;
}
.diag-counts .fail {
  color: #f87171;
}
.diag-item {
  background: #1e293b;
  margin-bottom: 8px;
  border-color: #334155;
}
.item-row {
  display: flex;
  gap: 10px;
  font-size: 12px;
}
.item-ico {
  font-size: 16px;
}
.item-sev {
  font-weight: 700;
}
.item-msg {
  color: #94a3b8;
  word-break: break-word;
}
.events-wrap {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 220px);
  min-height: 320px;
}
.events-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}
.events-log {
  flex: 1;
  overflow: auto;
  background: #0b1120;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 8px;
  font-family: ui-monospace, monospace;
  font-size: 11px;
}
.event-line {
  display: flex;
  gap: 8px;
  padding: 4px;
  margin-bottom: 2px;
  border-radius: 4px;
  align-items: flex-start;
}
.event-line.t-execution_start {
  background: rgba(59, 130, 246, 0.12);
}
.event-line.t-task_failed,
.event-line.t-sprint_failed,
.event-line.t-execution_failed {
  background: rgba(239, 68, 68, 0.1);
}
.ev-ts {
  color: #64748b;
  flex-shrink: 0;
}
.ev-type {
  color: #38bdf8;
  flex-shrink: 0;
  min-width: 120px;
}
.ev-msg {
  flex: 1;
  word-break: break-word;
  color: #cbd5e1;
}
</style>
