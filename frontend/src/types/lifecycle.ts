export interface LifecycleContract {
  execution_id: string
  stages: ContractStage[]
  transitions: ContractTransition[]
  state_machine: StateMachineDefinition
}

export interface ContractStage {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  entered_at?: number
  completed_at?: number
  activities: ContractActivity[]
}

export interface ContractActivity {
  id: string
  name: string
  type: string
  status: string
  result?: Record<string, unknown>
}

export interface ContractTransition {
  from: string
  to: string
  condition?: string
  triggered_at?: number
}

export interface StateMachineDefinition {
  states: Record<string, StateDefinition>
  initial: string
  transitions: Record<string, TransitionDefinition[]>
}

export interface StateDefinition {
  name: string
  type: 'normal' | 'final' | 'initial'
}

export interface TransitionDefinition {
  target: string
  event?: string
  guard?: string
}

export interface ContractReviewResult {
  success: boolean
  execution_id: string
  review_status: 'approved' | 'rejected' | 'pending'
  feedback?: string
}