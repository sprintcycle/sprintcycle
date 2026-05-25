import { defineStore } from 'pinia'
import { ref, watch, nextTick } from 'vue'
import { connectSSE, disconnectSSE, subscribeSSE } from '@/sse'
import { apiClients } from '@/api/platform'

export type EventLine = { type: string; ts: string; display: string; text: string; agent?: string }

export const useEventsStore = defineStore('events', () => {
  const sseLabel = ref('disconnected')
  const sseDotClass = ref<'off' | 'ok' | 'bad'>('off')
  const clientCount = ref(0)
  const liveEventCount = ref(0)
  const eventLines = ref<EventLine[]>([])
  const autoScrollEvents = ref(true)
  const eventsLogRef = ref<HTMLElement | null>(null)

  let unsubSSE: (() => void) | null = null
  let pollClients: ReturnType<typeof setInterval> | null = null

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

  function clearEvents() {
    eventLines.value = []
    liveEventCount.value = 0
  }

  function mountEvents() {
    wireSSE()
    pollClients = setInterval(refreshClients, 5000)
    void refreshClients()
  }

  function unmountEvents() {
    disconnectSSE({ keepListeners: false })
    unsubSSE?.()
    if (pollClients) clearInterval(pollClients)
    pollClients = null
  }

  return {
    sseLabel,
    sseDotClass,
    clientCount,
    liveEventCount,
    eventLines,
    autoScrollEvents,
    eventsLogRef,
    pushEvent,
    clearEvents,
    mountEvents,
    unmountEvents,
  }
})