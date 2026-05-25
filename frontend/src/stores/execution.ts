import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiStatus,
  apiPlan,
  apiRun,
  apiStop,
  apiRollback,
  apiExecutionTrace,
  apiExecutionReplay,
  apiDiagnose,
  looksLikeYaml,
} from '@/api/execution'
import type { Execution, ExecutionTrace, DiagnoseResult } from '@/types'

export const useExecutionStore = defineStore('execution', () => {
  const yamlInput = ref('')
  const referencePathsText = ref('')
  const writePolicy = ref('auto')
  const planBusy = ref(false)
  const planMeta = ref('')
  const planMessage = ref('点击 **Plan** 预览执行计划，或直接 **Run** 开始执行')
  const planTone = ref<'muted' | 'loading' | 'error' | 'ok'>('muted')

  const executions = ref<Execution[]>([])
  const historyLoaded = ref(false)
  const expanded = ref<Record<string, boolean>>({})
  const releaseFinalizationByExec = ref<Record<string, Record<string, unknown>>>({})
  const releaseFinalizationCurrent = ref<Record<string, unknown>>({})
  const tracePayload = ref<ExecutionTrace | null>(null)
  const replayPayload = ref<Record<string, unknown>>({})
  const lifecycleContracts = ref<Record<string, Record<string, unknown>>>({})

  const diagnoseLoading = ref(false)
  const diagnoseResult = ref<DiagnoseResult | null>(null)

  const historyBadge = computed(() => executions.value.length)

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
    } catch (e: unknown) {
      planTone.value = 'error'
      planMessage.value = `请求失败：${String(e)}`
    } finally {
      planBusy.value = false
    }
  }

  async function handleRun() {
    const { input, body } = planPayload()
    if (!input) {
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
    } catch (e: unknown) {
      planTone.value = 'error'
      planMessage.value = `请求失败：${String(e)}`
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
      if (!data.success) {
        throw new Error(String(data.error))
      }
      executions.value = data.executions || []
      
      const rf: Record<string, Record<string, unknown>> = {}
      for (const ex of executions.value) {
        const fin = ex.release_finalization
        if (ex.execution_id && fin) rf[ex.execution_id] = fin
      }
      releaseFinalizationByExec.value = rf
      releaseFinalizationCurrent.value = data.release_finalization || {}
      
      const latestId = data.primary_execution?.execution_id || executions.value[0]?.execution_id
      if (latestId) {
        await Promise.all([
          loadTrace(latestId),
          loadReplay(latestId),
          loadLifecycleContract(latestId),
        ])
      }
      historyLoaded.value = true
    } catch {
      /* ignore */
    }
  }

  async function loadTrace(executionId: string) {
    try {
      const data = await apiExecutionTrace(executionId)
      tracePayload.value = data.data || null
    } catch {
      tracePayload.value = null
    }
  }

  async function loadReplay(executionId: string) {
    try {
      const data = await apiExecutionReplay(executionId)
      replayPayload.value = data || {}
    } catch {
      replayPayload.value = {}
    }
  }

  async function loadLifecycleContract(executionId: string) {
    try {
      const data = await apiExecutionReplay(executionId)
      lifecycleContracts.value = { [executionId]: data || {} }
    } catch {
      lifecycleContracts.value = {}
    }
  }

  async function handleStop(execId: string) {
    await apiStop(execId)
    await loadHistory()
  }

  async function handleRollback(execId: string) {
    await apiRollback(execId)
    await loadHistory()
  }

  async function handleResume(execId: string) {
    const data = await apiRun({ execution_id: execId, resume: true })
    if (data.success === false) {
      throw new Error(String(data.error))
    }
    await loadHistory()
  }

  async function runDiagnose() {
    diagnoseLoading.value = true
    try {
      diagnoseResult.value = await apiDiagnose()
    } catch {
      diagnoseResult.value = null
    } finally {
      diagnoseLoading.value = false
    }
  }

  function toggleExpand(id: string) {
    expanded.value = { ...expanded.value, [id]: !expanded.value[id] }
  }

  function sprintRows(ex: Execution) {
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

  function finalizationForExec(ex: Execution) {
    const id = String(ex.execution_id)
    if (id && releaseFinalizationByExec.value[id]) return releaseFinalizationByExec.value[id]
    return releaseFinalizationCurrent.value
  }

  function shortId(id: string) {
    return id.length > 8 ? id.slice(0, 8) : id
  }

  function canResume(ex: Execution): boolean {
    const chk = ex.checkpoint
    return ['cancelled', 'failed', 'paused'].includes(ex.status) && !!chk
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
    releaseFinalizationByExec,
    releaseFinalizationCurrent,
    tracePayload,
    replayPayload,
    lifecycleContracts,
    diagnoseLoading,
    diagnoseResult,
    historyBadge,
    handlePlan,
    handleRun,
    clearEditor,
    loadHistory,
    loadTrace,
    loadReplay,
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
  }
})