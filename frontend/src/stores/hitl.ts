import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiHitlPending, apiHitlHistory, apiHitlSubmit } from '@/api/hitl'
import type { HitlRequest, HitlHistoryEntry } from '@/types'

export const useHitlStore = defineStore('hitl', () => {
  const hitlPending = ref<HitlRequest[]>([])
  const hitlHistory = ref<HitlHistoryEntry[]>([])
  const hitlNotes = ref<Record<string, string>>({})
  const hitlBusy = ref(false)

  let hitlPollTimer: ReturnType<typeof setInterval> | null = null

  async function loadHitl() {
    hitlBusy.value = true
    try {
      const p = await apiHitlPending()
      const h = await apiHitlHistory(undefined, 30)
      hitlPending.value = Array.isArray(p.data) ? p.data : []
      hitlHistory.value = Array.isArray(h.data) ? h.data : []
    } catch {
      /* ignore */
    } finally {
      hitlBusy.value = false
    }
  }

  async function submitHitlDecision(requestId: string, decision: string) {
    const note = hitlNotes.value[requestId]?.trim() || undefined
    const res = await apiHitlSubmit(requestId, decision, note)
    if (res.success === false) {
      throw new Error(String(res.error))
    }
    await loadHitl()
  }

  function startPolling() {
    if (hitlPollTimer) clearInterval(hitlPollTimer)
    hitlPollTimer = setInterval(() => void loadHitl(), 4000)
  }

  function stopPolling() {
    if (hitlPollTimer) {
      clearInterval(hitlPollTimer)
      hitlPollTimer = null
    }
  }

  return {
    hitlPending,
    hitlHistory,
    hitlNotes,
    hitlBusy,
    loadHitl,
    submitHitlDecision,
    startPolling,
    stopPolling,
  }
})