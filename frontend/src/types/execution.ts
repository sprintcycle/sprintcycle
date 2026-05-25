export interface Execution {
  execution_id: string
  status: ExecutionStatus
  mode: string
  release_plan_name?: string
  timestamp: number
  duration?: number
  sprint_history: Sprint[]
  release_finalization?: Record<string, unknown>
  metadata?: Record<string, unknown>
  checkpoint?: Record<string, unknown>
}

export type ExecutionStatus = 
  | 'running' 
  | 'completed' 
  | 'failed' 
  | 'cancelled' 
  | 'paused'

export interface Sprint {
  name: string
  status: string
  tasks: Task[]
  task_results?: TaskResult[]
}

export interface Task {
  id?: string
  name: string
  type?: string
  description?: string
}

export interface TaskResult {
  task_name: string
  status: 'success' | 'failed' | 'skipped'
  duration?: number
  error?: string
  output?: string
}

export interface ExecutionTrace {
  run_id: string
  events: TraceEvent[]
}

export interface TraceEvent {
  timestamp: number
  type: string
  data: Record<string, unknown>
}

export interface DiagnoseResult {
  success: boolean
  health_score: number
  issues: DiagnoseIssue[]
  coverage?: number
  complexity?: Record<string, unknown>
  duration?: number
}

export interface DiagnoseIssue {
  id: string
  severity: 'pass' | 'warn' | 'fail' | 'info'
  title: string
  description: string
  category?: string
  suggestion?: string
}