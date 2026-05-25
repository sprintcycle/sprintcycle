import axios from 'axios'
import type { HitlRequest, HitlHistoryEntry } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiHitlPending(executionId?: string) {
  const { data } = await api.get<{ data: HitlRequest[] }>('/hitl/pending', {
    params: executionId ? { execution_id: executionId } : {},
  })
  return data
}

export async function apiHitlHistory(executionId?: string, limit = 50) {
  const { data } = await api.get<{ data: HitlHistoryEntry[] }>('/hitl/history', {
    params: {
      ...(executionId ? { execution_id: executionId } : {}),
      limit,
    },
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

export async function apiHitlShow(requestId: string) {
  const { data } = await api.get<Record<string, unknown>>(`/hitl/${encodeURIComponent(requestId)}`)
  return data
}