export interface Suggestion {
  id: string
  type: SuggestionType
  status: SuggestionStatus
  title: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  source_id?: string
  metadata?: Record<string, unknown>
  created_at: number
  updated_at?: number
  reviewer?: string
  notes?: string
}

export type SuggestionType = 
  | 'code_fix' 
  | 'refactor' 
  | 'security' 
  | 'performance' 
  | 'quality'

export type SuggestionStatus = 
  | 'pending' 
  | 'reviewing' 
  | 'approved' 
  | 'rejected' 
  | 'archived' 
  | 'promoted'

export interface SuggestionOverview {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  recent: Suggestion[]
}

export interface SuggestionActionResult {
  success: boolean
  suggestion_id: string
  status: SuggestionStatus
  message?: string
}