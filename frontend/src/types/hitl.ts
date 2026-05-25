export interface HitlRequest {
  request_id: string
  execution_id?: string
  type: HitlRequestType
  status: HitlRequestStatus
  title: string
  description: string
  context: Record<string, unknown>
  created_at: number
  resolved_at?: number
  decision?: string
  note?: string
}

export type HitlRequestType = 
  | 'approval' 
  | 'review' 
  | 'confirmation' 
  | 'input'

export type HitlRequestStatus = 
  | 'open' 
  | 'resolved' 
  | 'cancelled'

export interface HitlDecision {
  request_id: string
  decision: string
  note?: string
}

export interface HitlHistoryEntry {
  request_id: string
  execution_id?: string
  type: string
  title: string
  decision: string
  timestamp: number
  status: string
}