import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  apiSuggestionApprove,
  apiSuggestionReject,
  apiSuggestionReview,
  apiSuggestionArchive,
  apiSuggestionsBoard,
} from '@/api/suggestions'
import type { Suggestion } from '@/types'

export const useSuggestionsStore = defineStore('suggestions', () => {
  const fixSuggestions = ref<Suggestion[]>([])
  const promotionLog = ref<Suggestion[]>([])
  const selectedFixSuggestion = ref<Suggestion | null>(null)
  const selectedLinkedRunId = ref<string>('')

  async function loadSuggestions(executionId?: string) {
    try {
      const fix = await apiSuggestionsBoard(executionId, 20)
      const data = fix as { suggestions?: Suggestion[] }
      fixSuggestions.value = Array.isArray(data?.suggestions) ? data.suggestions : []
      promotionLog.value = fixSuggestions.value.filter((item) => String(item.status ?? '') === 'promoted')
    } catch {
      fixSuggestions.value = []
      promotionLog.value = []
    }
  }

  async function approveSuggestion(suggestionId: string) {
    const res = await apiSuggestionApprove(suggestionId, 'dashboard')
    if (res.success === false) {
      throw new Error(String(res.error))
    }
    await loadSuggestions()
  }

  async function rejectSuggestion(suggestionId: string) {
    const res = await apiSuggestionReject(suggestionId, 'dashboard')
    if (res.success === false) {
      throw new Error(String(res.error))
    }
    await loadSuggestions()
  }

  async function reviewSuggestion(suggestionId: string) {
    const res = await apiSuggestionReview(suggestionId)
    if (res.success === false) {
      throw new Error(String(res.error))
    }
    await loadSuggestions()
  }

  async function archiveSuggestion(suggestionId: string) {
    const res = await apiSuggestionArchive(suggestionId)
    if (res.success === false) {
      throw new Error(String(res.error))
    }
    await loadSuggestions()
  }

  function selectSuggestion(item: Suggestion | null) {
    selectedFixSuggestion.value = item
    const runId = item ? String(item.metadata?.run_id ?? item.source_id ?? '') : ''
    selectedLinkedRunId.value = runId
  }

  return {
    fixSuggestions,
    promotionLog,
    selectedFixSuggestion,
    selectedLinkedRunId,
    loadSuggestions,
    approveSuggestion,
    rejectSuggestion,
    reviewSuggestion,
    archiveSuggestion,
    selectSuggestion,
  }
})