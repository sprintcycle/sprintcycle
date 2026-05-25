import axios from 'axios'
import type { Execution, ExecutionTrace, DiagnoseResult } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export function looksLikeYaml(text: string): boolean {
  return /^(project|sprints|mode|name|version)\s*:/im.test(text)
}

export async function apiPlan(body: Record<string, unknown>) {
  const { data } = await api.post<Record<string, unknown>>('/v1/plan', body)
  return data
}

export async function apiRun(body: Record<string, unknown>) {
  const { data } = await api.post<Record<string, unknown>>('/v1/run', body)
  return data
}

export async function apiStatus(executionId?: string) {
  const { data } = await api.post<{
    success: boolean
    executions?: Execution[]
    release_finalization?: Record<string, unknown>
    primary_execution?: Execution
  }>('/v1/status', executionId ? { execution_id: executionId } : {})
  return data
}

export async function apiStop(executionId: string) {
  const { data } = await api.post<Record<string, unknown>>('/v1/stop', { execution_id: executionId })
  return data
}

export async function apiRollback(executionId: string) {
  const { data } = await api.post<Record<string, unknown>>('/v1/rollback', { execution_id: executionId })
  return data
}

export async function apiExecutionTrace(executionId: string) {
  const { data } = await api.get<{ data: ExecutionTrace }>('/execution/trace', {
    params: { execution_id: executionId },
  })
  return data
}

export async function apiExecutionDetail(executionId: string, limit = 200) {
  const { data } = await api.get<Record<string, unknown>>(
    `/execution/${encodeURIComponent(executionId)}/detail`,
    { params: { limit } },
  )
  return data
}

export async function apiExecutionReplay(executionId: string, limit = 500) {
  const { data } = await api.get<Record<string, unknown>>(
    `/execution/${encodeURIComponent(executionId)}/replay`,
    { params: { limit } },
  )
  return data
}

export async function apiDiagnose(): Promise<DiagnoseResult> {
  const { data } = await api.get<DiagnoseResult>('/execution/diagnose')
  return data
}