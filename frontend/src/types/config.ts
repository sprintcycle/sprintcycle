export interface ConfigApiEnvelope {
  success?: boolean
  data?: Record<string, unknown>
  error?: string
  detail?: unknown
}

export interface ConfigHistoryEntry {
  timestamp: number
  source: string
  updates: Record<string, unknown>
}