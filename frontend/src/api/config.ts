import axios from 'axios'
import type { ConfigApiEnvelope, ConfigHistoryEntry } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiConfigGet(): Promise<ConfigApiEnvelope> {
  const { data } = await api.get<ConfigApiEnvelope>('/config')
  return data
}

export async function apiConfigSchema(): Promise<ConfigApiEnvelope> {
  const { data } = await api.get<ConfigApiEnvelope>('/config/schema')
  return data
}

export async function apiConfigHistory(): Promise<{ data: ConfigHistoryEntry[] }> {
  const { data } = await api.get<{ data: ConfigHistoryEntry[] }>('/config/history')
  return data
}

export async function apiConfigPut(body: { updates: Record<string, unknown> }): Promise<ConfigApiEnvelope> {
  const { data } = await api.put<ConfigApiEnvelope>('/config', body)
  return data
}

export async function apiConfigImport(config: Record<string, unknown>): Promise<ConfigApiEnvelope> {
  const { data } = await api.post<ConfigApiEnvelope>('/config/import', { config })
  return data
}

export async function apiConfigReload(): Promise<ConfigApiEnvelope> {
  const { data } = await api.post<ConfigApiEnvelope>('/config/reload', {})
  return data
}