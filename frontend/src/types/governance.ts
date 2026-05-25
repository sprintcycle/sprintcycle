export interface GovernanceReport {
  success: boolean
  gate: string
  planning?: GovernanceGateReport
  review?: GovernanceGateReport
  should_fail_ci?: boolean
}

export interface GovernanceGateReport {
  gate: string
  status: 'pass' | 'fail' | 'warn'
  checks: GovernanceCheck[]
  timestamp: number
  duration?: number
}

export interface GovernanceCheck {
  id: string
  rule_id: string
  status: 'pass' | 'fail' | 'warn'
  message: string
  details?: Record<string, unknown>
  severity?: string
}

export interface GovernanceHistoryEntry {
  id: string
  timestamp: number
  gate: string
  status: string
  summary: Record<string, unknown>
}

export interface GovernanceLifecycleSummary {
  execution_id?: string
  stages: LifecycleStage[]
  overall_status: string
}

export interface LifecycleStage {
  name: string
  status: string
  timestamp?: number
  checks?: GovernanceCheck[]
}