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

export async function apiDiagnose() {
  const { data } = await api.get<Record<string, unknown>>('/diagnose')
  return data
}

export async function apiClients() {
  const { data } = await api.get<{ client_count?: number }>('/clients')
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
