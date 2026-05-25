import axios from 'axios'
import type { GovernanceReport, GovernanceHistoryEntry, GovernanceLifecycleSummary } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiGovernanceLatest() {
  const { data } = await api.get<Record<string, unknown>>('/governance/latest')
  return data
}

export async function apiGovernanceHistory(limit = 50) {
  const { data } = await api.get<{ entries?: GovernanceHistoryEntry[] }>('/governance/history', {
    params: { limit },
  })
  return data
}

export async function apiGovernanceCheck(gate: 'review' | 'planning' | 'both' = 'review'): Promise<GovernanceReport> {
  const { data } = await api.post<GovernanceReport>('/governance/check', { gate })
  return data
}

export async function apiGovernanceLifecycle(executionId?: string): Promise<GovernanceLifecycleSummary> {
  const { data } = await api.get<GovernanceLifecycleSummary>('/governance/lifecycle', {
    params: executionId ? { execution_id: executionId } : {},
  })
  return data
}