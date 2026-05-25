import axios from 'axios'
import type { LifecycleContract, ContractReviewResult } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiLifecycleContract(executionId: string, limit = 200) {
  const { data } = await api.get<{ data: LifecycleContract }>('/lifecycle/contract', {
    params: { execution_id: executionId, limit },
  })
  return data
}

export async function apiLifecycleContractReview(executionId: string, body: Record<string, unknown> = {}): Promise<ContractReviewResult> {
  const { data } = await api.post<ContractReviewResult>(
    `/lifecycle/contract/${encodeURIComponent(executionId)}/review`,
    body,
  )
  return data
}

export async function apiLifecycleDelivery() {
  const { data } = await api.get<Record<string, unknown>>('/lifecycle/delivery')
  return data
}