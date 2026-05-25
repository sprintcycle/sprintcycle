export interface PlatformOverview {
  version: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  uptime: number
  components: PlatformComponent[]
}

export interface PlatformComponent {
  name: string
  status: 'running' | 'stopped' | 'error' | 'warning'
  version?: string
  uptime?: number
}

export interface FitnessScore {
  overall: number
  dimensions: FitnessDimension[]
}

export interface FitnessDimension {
  name: string
  score: number
  weight?: number
  details?: Record<string, unknown>
}

export interface DeployStatus {
  environment: string
  status: DeployStatusType
  last_deployed_at?: number
  version?: string
  commit?: string
}

export type DeployStatusType = 
  | 'deploying' 
  | 'deployed' 
  | 'failed' 
  | 'pending'