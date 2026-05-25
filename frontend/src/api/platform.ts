import axios from 'axios'
import type { PlatformOverview, FitnessScore, DeployStatus } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiPlatformOverview(): Promise<PlatformOverview> {
  const { data } = await api.get<PlatformOverview>('/platform/overview')
  return data
}

export async function apiPlatformFitness(): Promise<{ data: FitnessScore }> {
  const { data } = await api.get<{ data: FitnessScore }>('/platform/fitness')
  return data
}

export async function apiPlatformDeploy(): Promise<{ data: DeployStatus }> {
  const { data } = await api.get<{ data: DeployStatus }>('/platform/deploy')
  return data
}

export async function apiClients() {
  const { data } = await api.get<{ client_count?: number }>('/clients')
  return data
}