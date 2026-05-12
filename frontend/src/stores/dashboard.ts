import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { defineStore } from 'pinia'
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import {
  apiClients,
  apiDashboardFix,
  apiDashboardReplay,
  apiDashboardTrace,
  apiDiagnose,
  apiHitlHistory,
  apiHitlPending,
  apiHitlSubmit,
  apiPlan,
  apiPlatformSummary,
  apiRollback,
  apiRun,
  apiStatus,
  apiStop,
  apiSuggestionApprove,
  apiSuggestionArchive,
  apiSuggestionReject,
  apiSuggestionReview,
  looksLikeYaml,
} from '@/api'
import { connectSSE, disconnectSSE, subscribeSSE } from '@/sse'

export type EventLine = { type: string; ts: string; display: string; text: string; agent?: string }

export const useDashboardStore = defineStore('dashboard', () => {
  const router = useRouter()
  const yamlInput = ref('')
  /** 参考项目路径，一行一个（可选） */
  const referencePathsText = ref('')
  /** auto | create | incremental | safe */
  const writePolicy = ref('auto')
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
  let hitlPollTimer: ReturnType<typeof setInterval> | null = null

  const hitlPending = ref<Record<string, unknown>[]>([])
  const hitlHistory = ref<Record<string, unknown>[]>([])
  const hitlNotes = ref<Record<string, string>>({})
  const hitlBusy = ref(false)

  const historyBadge = computed(() => executions.value.length)
  const releaseFinalizationByExec = ref<Record<string, Record<string, unknown>>>({})
  const releaseFinalizationCurrent = ref<Record<string, unknown>>({})
  const tracePayload = ref<Record<string, unknown>>({})
  const replayPayload = ref<Record<string, unknown>>({})
  const fixSuggestions = ref<Record<string, unknown>[]>([])
  const promotionLog = ref<Record<string, unknown>[]>([])
  const deployPayload = ref<Record<string, unknown>>({})
  const selectedTraceNode = ref<Record<string, unknown> | null>(null)
  const selectedFixSuggestion = ref<Record<string, unknown> | null>(null)
  const selectedLinkedRunId = ref<string>('')

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
    hitl_request_open: { icon: '✋', label: 'HITL 待决策' },
    hitl_request_resolved: { icon: '✔', label: 'HITL 已决策' },
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
    if (typeof data.title === 'string') parts.push(data.title)
    if (typeof data.summary === 'string') parts.push(data.summary.slice(0, 120))
    if (typeof data.request_id === 'string') parts.push(`#${data.request_id.slice(0, 8)}`)
    if (typeof data.decision === 'string') parts.push(`→ ${data.decision}`)
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
    const agent = typeof data.agent_type === 'string' ? data.agent_type : undefined
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
    const base = looksLikeYaml(input) ? { release_plan_yaml: input } : { intent: input }
    const refs = referencePathsText.value
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    const body: Record<string, unknown> = {
      ...base,
      write_policy: writePolicy.value || 'auto',
    }
    if (refs.length) body.reference_paths = refs
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
      const rf: Record<string, Record<string, unknown>> = {}
      for (const ex of executions.value) {
        const id = String(ex.execution_id ?? '')
        const fin = ex.release_finalization
        if (id && fin && typeof fin === 'object') rf[id] = fin as Record<string, unknown>
      }
      releaseFinalizationByExec.value = rf
      const current = data.release_finalization
      releaseFinalizationCurrent.value =
        current && typeof current === 'object' ? (current as Record<string, unknown>) : {}
      const latestId = String(data.primary_execution?.execution_id ?? executions.value[0]?.execution_id ?? '')
      if (latestId) {
        try {
          const trace = await apiDashboardTrace(latestId)
          tracePayload.value = (trace.data as Record<string, unknown>) || {}
        } catch {
          tracePayload.value = {}
        }
        try {
          const replay = await apiDashboardReplay(latestId)
          replayPayload.value = (replay.data as Record<string, unknown>) || {}
        } catch {
          replayPayload.value = {}
        }
      }
      try {
        const fix = await apiDashboardFix()
        const data = fix.data as { suggestions?: Record<string, unknown>[] } | undefined
        fixSuggestions.value = Array.isArray(data?.suggestions) ? data!.suggestions! : []
        promotionLog.value = fixSuggestions.value.filter((item) => String(item.status ?? '') === 'promoted')
      } catch {
        fixSuggestions.value = []
        promotionLog.value = []
      }
      try {
        const deploy = await apiPlatformSummary()
        deployPayload.value = (deploy as Record<string, unknown>) || {}
      } catch {
        deployPayload.value = {}
      }
      historyLoaded.value = true
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  function toggleExpand(id: string) {
    expanded.value = { ...expanded.value, [id]: !expanded.value[id] }
  }

  function selectTraceNode(node: Record<string, unknown> | null) {
    selectedTraceNode.value = node
    const runId = node ? String(node.run_id ?? node.data?.run_id ?? node.event?.run_id ?? '') : ''
    selectedLinkedRunId.value = runId
    if (runId) void router.push({ name: 'fix' })
  }

  function selectFixSuggestion(item: Record<string, unknown> | null) {
    selectedFixSuggestion.value = item
    const runId = item ? String(item.metadata?.run_id ?? item.source_id ?? item.metadata?.event?.run_id ?? '') : ''
    selectedLinkedRunId.value = runId
    if (runId) void router.push({ name: 'trace' })
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

  function finalizationForExec(ex: Record<string, unknown>) {
    const id = String(ex.execution_id ?? '')
    if (id && releaseFinalizationByExec.value[id]) return releaseFinalizationByExec.value[id]
    return releaseFinalizationCurrent.value
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

  async function handleRollback(execId: string) {
    try {
      await ElMessageBox.confirm(
        `确认回滚执行 ${shortId(execId)}？将尝试恢复到记录的备份点。`,
        '确认回滚',
        { type: 'warning' },
      )
    } catch {
      return
    }
    try {
      const data = await apiRollback(execId)
      if (data.success === false) {
        ElMessage.error(String(data.error ?? '回滚失败'))
        return
      }
      const pt = typeof data.rollback_point === 'string' ? data.rollback_point : ''
      ElMessage.success(pt ? `已回滚 · ${pt}` : '回滚已完成')
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
      const { router } = await import('@/router')
      await router.push({ name: 'events' })
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

  async function loadHitl() {
    hitlBusy.value = true
    try {
      const p = await apiHitlPending()
      const h = await apiHitlHistory(undefined, 30)
      hitlPending.value = Array.isArray(p.data) ? (p.data as Record<string, unknown>[]) : []
      hitlHistory.value = Array.isArray(h.data) ? (h.data as Record<string, unknown>[]) : []
    } catch {
      /* ignore */
    } finally {
      hitlBusy.value = false
    }
  }

  async function submitHitlDecision(requestId: string, decision: string) {
    try {
      const note = hitlNotes.value[requestId]?.trim() || undefined
      const res = await apiHitlSubmit(requestId, decision, note)
      if (res.success === false) {
        ElMessage.error(String(res.error ?? '提交失败'))
        return
      }
      ElMessage.success('决策已提交')
      await loadHitl()
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  async function approveSuggestion(suggestionId: string) {
    try {
      const res = await apiSuggestionApprove(suggestionId, 'dashboard', hitlNotes.value[suggestionId] || undefined)
      if (res.success === false) {
        ElMessage.error(String(res.error ?? '批准失败'))
        return
      }
      ElMessage.success('建议已批准')
      await loadHistory()
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  async function rejectSuggestion(suggestionId: string) {
    try {
      const res = await apiSuggestionReject(suggestionId, 'dashboard', hitlNotes.value[suggestionId] || undefined)
      if (res.success === false) {
        ElMessage.error(String(res.error ?? '拒绝失败'))
        return
      }
      ElMessage.success('建议已拒绝')
      await loadHistory()
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  async function reviewSuggestion(suggestionId: string) {
    try {
      const res = await apiSuggestionReview(suggestionId)
      if (res.success === false) {
        ElMessage.error(String(res.error ?? '复审失败'))
        return
      }
      ElMessage.success('建议已进入复审')
      await loadHistory()
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  async function archiveSuggestion(suggestionId: string) {
    try {
      const res = await apiSuggestionArchive(suggestionId)
      if (res.success === false) {
        ElMessage.error(String(res.error ?? '归档失败'))
        return
      }
      ElMessage.success('建议已归档')
      await loadHistory()
    } catch (e) {
      ElMessage.error(fmtErr(e))
    }
  }

  function onRouteChange(name: string | symbol | undefined | null) {
    const n = typeof name === 'string' ? name : ''
    if (n === 'history') void loadHistory()
    if (hitlPollTimer) {
      clearInterval(hitlPollTimer)
      hitlPollTimer = null
    }
    if (n === 'hitl') {
      void loadHitl()
      hitlPollTimer = setInterval(() => void loadHitl(), 4000)
    }
  }

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

  function mountDashboard() {
    document.documentElement.classList.add('dark')
    wireSSE()
    pollClients = setInterval(refreshClients, 5000)
    void refreshClients()
    void loadHistory()
  }

  function unmountDashboard() {
    disconnectSSE({ keepListeners: false })
    unsubSSE?.()
    if (pollClients) clearInterval(pollClients)
    if (hitlPollTimer) clearInterval(hitlPollTimer)
    pollClients = null
    hitlPollTimer = null
  }

  return {
    yamlInput,
    referencePathsText,
    writePolicy,
    planBusy,
    planMeta,
    planMessage,
    planTone,
    executions,
    historyLoaded,
    expanded,
    diagnoseLoading,
    diagnoseScore,
    diagnoseTitle,
    diagnoseDesc,
    diagnoseIssues,
    diagnoseStats,
    sseLabel,
    sseDotClass,
    clientCount,
    liveEventCount,
    eventLines,
    autoScrollEvents,
    eventsLogRef,
    hitlPending,
    hitlHistory,
    hitlNotes,
    hitlBusy,
    historyBadge,
    releaseFinalizationByExec,
    releaseFinalizationCurrent,
    tracePayload,
    replayPayload,
    promotionLog,
    deployPayload,
    selectedTraceNode,
    selectedFixSuggestion,
    selectedLinkedRunId,
    handlePlan,
    handleRun,
    clearEditor,
    loadHistory,
    toggleExpand,
    sprintRows,
    taskRows,
    finalizationForExec,
    shortId,
    canResume,
    handleStop,
    handleRollback,
    handleResume,
    runDiagnose,
    clearEvents,
    loadHitl,
    submitHitlDecision,
    approveSuggestion,
    rejectSuggestion,
    reviewSuggestion,
    archiveSuggestion,
    onRouteChange,
    scoreColor,
    issueIcon,
    mountDashboard,
    unmountDashboard,
  }
})
