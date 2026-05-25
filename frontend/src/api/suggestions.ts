import axios from 'axios'
import type { Suggestion, SuggestionOverview, SuggestionActionResult } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 3_600_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function apiSuggestionApprove(suggestionId: string, approver: string, notes?: string) {
  const { data } = await api.post<SuggestionActionResult>(
    `/suggestions/${encodeURIComponent(suggestionId)}/approve`,
    { approver, notes: notes || undefined },
  )
  return data
}

export async function apiSuggestionReject(suggestionId: string, approver: string, notes?: string) {
  const { data } = await api.post<SuggestionActionResult>(
    `/suggestions/${encodeURIComponent(suggestionId)}/reject`,
    { approver, notes: notes || undefined },
  )
  return data
}

export async function apiSuggestionReview(suggestionId: string) {
  const { data } = await api.post<SuggestionActionResult>(
    `/suggestions/${encodeURIComponent(suggestionId)}/review`,
    {},
  )
  return data
}

export async function apiSuggestionArchive(suggestionId: string) {
  const { data } = await api.post<SuggestionActionResult>(
    `/suggestions/${encodeURIComponent(suggestionId)}/archive`,
    {},
  )
  return data
}

export async function apiSuggestionsOverview(): Promise<SuggestionOverview> {
  const { data } = await api.get<SuggestionOverview>('/suggestions/overview')
  return data
}

export async function apiSuggestionsBoard(executionId?: string, limit = 20) {
  const { data } = await api.get<{ suggestions?: Suggestion[] }>('/suggestions/board', {
    params: {
      ...(executionId ? { execution_id: executionId } : {}),
      limit,
    },
  })
  return data
}