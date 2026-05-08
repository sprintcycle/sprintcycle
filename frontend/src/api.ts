import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export function looksLikeYaml(text: string): boolean {
  return /^(project|sprints|mode|name|version)\s*:/im.test(text)
}

export async function apiPlan(body: Record<string, unknown>) {
  const { data } = await api.post<Record<string, unknown>>('/plan', body)
  return data
}

export async function apiRun(body: Record<string, unknown>) {
  const { data } = await api.post<Record<string, unknown>>('/run', body)
  return data
}

export async function apiStatus(executionId?: string) {
  const { data } = await api.post<Record<string, unknown>>(
    '/status',
    executionId ? { execution_id: executionId } : {},
  )
  return data
}

export async function apiStop(executionId: string) {
  const { data } = await api.post<Record<string, unknown>>('/stop', { execution_id: executionId })
  return data
}

export async function apiRollback(executionId: string) {
  const { data } = await api.post<Record<string, unknown>>('/rollback', { execution_id: executionId })
  return data
}

export async function apiDiagnose() {
  const { data } = await api.get<Record<string, unknown>>('/diagnose')
  return data
}

export async function apiGovernanceLatest() {
  const { data } = await api.get<Record<string, unknown>>('/governance/latest')
  return data
}

export async function apiGovernanceHistory(limit = 50) {
  const { data } = await api.get<{ entries?: unknown[] }>('/governance/history', {
    params: { limit },
  })
  return data
}

export async function apiGovernanceCheck(gate: 'review' | 'planning' | 'both' = 'review') {
  const { data } = await api.post<Record<string, unknown>>('/governance/check', { gate })
  return data
}

export async function apiClients() {
  const { data } = await api.get<{ client_count?: number }>('/clients')
  return data
}

export async function apiPlatformSummary() {
  const { data } = await api.get<Record<string, unknown>>('/platform/summary')
  return data
}

export async function apiConsoleOverview(limit = 20) {
  const { data } = await api.get<Record<string, unknown>>('/console/overview', {
    params: { limit },
  })
  return data
}

export async function apiExecutionReplay(executionId: string, limit = 500) {
  const { data } = await api.get<Record<string, unknown>>(
    `/execution/${encodeURIComponent(executionId)}/replay`,
    { params: { limit } },
  )
  return data
}

export async function apiExecutionDetail(executionId: string, limit = 200) {
  const { data } = await api.get<Record<string, unknown>>(
    `/execution/${encodeURIComponent(executionId)}/detail`,
    { params: { limit } },
  )
  return data
}

export async function apiHitlPending(executionId?: string) {
  const { data } = await api.get<Record<string, unknown>>('/hitl/pending', {
    params: executionId ? { execution_id: executionId } : {},
  })
  return data
}

export async function apiHitlSubmit(requestId: string, decision: string, note?: string) {
  const { data } = await api.post<Record<string, unknown>>(
    `/hitl/${encodeURIComponent(requestId)}/decision`,
    { decision, note: note || undefined },
  )
  return data
}

export async function apiHitlHistory(executionId?: string, limit = 50) {
  const { data } = await api.get<Record<string, unknown>>('/hitl/history', {
    params: {
      ...(executionId ? { execution_id: executionId } : {}),
      limit,
    },
  })
  return data
}

export type ConfigApiEnvelope = {
  success?: boolean
  data?: Record<string, unknown>
  error?: string
  detail?: unknown
}

export async function apiConfigGet() {
  const { data } = await api.get<ConfigApiEnvelope>('/config')
  return data
}

export async function apiConfigSchema() {
  const { data } = await api.get<ConfigApiEnvelope>('/config/schema')
  return data
}

export async function apiConfigHistory() {
  const { data } = await api.get<ConfigApiEnvelope>('/config/history')
  return data
}

export async function apiConfigPut(body: { updates: Record<string, unknown> }) {
  const { data } = await api.put<ConfigApiEnvelope>('/config', body)
  return data
}

export async function apiConfigImport(config: Record<string, unknown>) {
  const { data } = await api.post<ConfigApiEnvelope>('/config/import', { config })
  return data
}

export async function apiConfigReload() {
  const { data } = await api.post<ConfigApiEnvelope>('/config/reload', {})
  return data
}
