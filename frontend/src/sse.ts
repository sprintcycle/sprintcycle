const EVENT_TYPES = [
  'execution_start',
  'sprint_start',
  'sprint_complete',
  'sprint_failed',
  'task_start',
  'task_complete',
  'task_failed',
  'governance_task_check',
  'governance_gate',
  'execution_complete',
  'execution_failed',
  'evolution_candidate',
  'heartbeat',
  'ping',
  'connected',
  'config_changed',
] as const

type Listener = (type: string, data: Record<string, unknown>) => void

let es: EventSource | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let attempts = 0
const maxAttempts = 12
const listeners = new Set<Listener>()
let connected = false

export function subscribeSSE(handler: Listener) {
  listeners.add(handler)
  return () => {
    listeners.delete(handler)
  }
}

function emit(type: string, data: Record<string, unknown>) {
  listeners.forEach((h) => {
    h(type, data)
  })
}

function clearReconnect() {
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function scheduleReconnect() {
  if (reconnectTimer !== null) return
  if (attempts >= maxAttempts) {
    emit('_error', { message: 'SSE: 已达最大重连次数' })
    return
  }
  const delay = Math.min(1000 * 2 ** attempts, 30_000)
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    attempts += 1
    connectSSE()
  }, delay)
}

export function connectSSE() {
  disconnectSSE({ keepListeners: true })
  es = new EventSource('/api/events/stream')
  es.onopen = () => {
    attempts = 0
    connected = true
    clearReconnect()
    emit('_open', {})
  }
  es.onerror = () => {
    connected = false
    emit('_close', {})
    if (es?.readyState === EventSource.CLOSED) {
      scheduleReconnect()
    }
  }
  for (const type of EVENT_TYPES) {
    es.addEventListener(type, (ev: Event) => {
      const msg = ev as MessageEvent
      try {
        const data = JSON.parse(String(msg.data)) as Record<string, unknown>
        if (type !== 'connected') emit(type, data)
      } catch {
        /* ignore malformed */
      }
    })
  }
}

export function disconnectSSE(opts?: { keepListeners?: boolean }) {
  clearReconnect()
  if (es) {
    es.close()
    es = null
  }
  connected = false
  if (!opts?.keepListeners) {
    listeners.clear()
  }
}

export function sseIsConnected() {
  return connected
}
