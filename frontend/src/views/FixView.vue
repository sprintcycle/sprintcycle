<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'

import { useSuggestionsStore } from '@/stores/suggestions'

const store = useSuggestionsStore()
const { suggestions, selectedSuggestion } = storeToRefs(store)

const stats = computed(() => {
  const total = suggestions.value.length
  const promoted = suggestions.value.filter((item) => String(item.status ?? '') === 'promoted').length
  const approved = suggestions.value.filter((item) => String(item.status ?? '') === 'approved').length
  const pending = suggestions.value.filter((item) => String(item.status ?? '') === 'pending').length
  return { total, promoted, approved, pending }
})

const localSelected = ref<Record<string, unknown> | null>(null)
const selectedCardEl = ref<HTMLElement | null>(null)

watch(selectedSuggestion, (val) => {
  localSelected.value = val
}, { immediate: true })

async function selectSuggestion(item: Record<string, unknown>) {
  localSelected.value = item
  store.selectSuggestion(item)
  await nextTick()
  selectedCardEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

onMounted(() => void store.loadSuggestions())
</script>

<template>
  <div class="fix-console">
    <div class="fix-hero">
      <div>
        <div class="eyebrow">ODD · Fix Console</div>
        <h2>问题驱动修复控制台</h2>
        <p class="fix-subtitle">把异常、建议、审批与推进做成卡片化操作面板，支持一键进入治理动作。</p>
      </div>
      <div class="fix-stats">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">Suggestions</div>
        </el-card>
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.promoted }}</div>
          <div class="stat-label">Promoted</div>
        </el-card>
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.approved }}</div>
          <div class="stat-label">Approved</div>
        </el-card>
      </div>
    </div>

    <div class="fix-toolbar">
      <el-tag type="warning" effect="dark">Pending {{ stats.pending }}</el-tag>
      <el-tag type="success" effect="dark">Approved {{ stats.approved }}</el-tag>
      <el-tag type="info" effect="dark">Promoted {{ stats.promoted }}</el-tag>
    </div>

    <div v-if="suggestions.length === 0" class="empty-state">暂无建议</div>
    <div v-else class="fix-grid">
      <el-card v-for="item in suggestions" :key="String(item.suggestion_id ?? item.title ?? '')" ref="selectedCardEl" shadow="never" class="fix-card" :class="{ selected: localSelected?.suggestion_id === item.suggestion_id }" @click="selectSuggestion(item)">
        <template #header>
          <div class="fix-card-head">
            <div class="fix-card-title">{{ item.title }}</div>
            <el-tag :type="item.status === 'promoted' ? 'success' : item.status === 'approved' ? 'primary' : 'warning'" effect="dark">
              {{ item.status }}
            </el-tag>
          </div>
        </template>

        <div class="fix-meta-row">
          <span class="severity-pill">{{ item.severity }}</span>
          <span class="sc-muted">source: {{ item.source_type }}</span>
        </div>
        <p class="fix-summary">{{ item.summary }}</p>
        <pre class="fix-detail">{{ item.details }}</pre>

        <div v-if="item.linked_evolution_id" class="fix-link">
          <span class="sc-muted">evolution</span>
          <b>{{ item.linked_evolution_id }}</b>
        </div>

        <div class="fix-actions">
          <el-button size="small" type="success" @click.stop="store.approveSuggestion(String(item.suggestion_id))">批准并推进</el-button>
          <el-button size="small" @click.stop="store.reviewSuggestion(String(item.suggestion_id))">复审</el-button>
          <el-button size="small" type="danger" @click.stop="store.rejectSuggestion(String(item.suggestion_id))">拒绝</el-button>
          <el-button size="small" @click.stop="store.archiveSuggestion(String(item.suggestion_id))">归档</el-button>
        </div>
      </el-card>

      <el-card v-if="localSelected" shadow="never" class="fix-detail-panel">
        <template #header>
          <div class="fix-card-head">
            <div class="fix-card-title">Selected Suggestion</div>
            <el-tag type="info" effect="dark">detail</el-tag>
          </div>
        </template>
        <div class="detail-block">
          <div><span class="sc-muted">ID</span><b>{{ localSelected.suggestion_id }}</b></div>
          <div><span class="sc-muted">Title</span><b>{{ localSelected.title }}</b></div>
          <div><span class="sc-muted">Status</span><b>{{ localSelected.status }}</b></div>
          <div><span class="sc-muted">Severity</span><b>{{ localSelected.severity }}</b></div>
          <div><span class="sc-muted">Evolution</span><b>{{ localSelected.linked_evolution_id || '—' }}</b></div>
          <div class="detail-json"><pre>{{ JSON.stringify(localSelected, null, 2) }}</pre></div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.fix-console {
  padding: 18px 20px 40px;
  display: grid;
  gap: 16px;
}
.fix-hero {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}
.eyebrow {
  color: #f59e0b;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
h2 {
  margin: 8px 0 6px;
  color: #f8fafc;
}
.fix-subtitle {
  margin: 0;
  color: #94a3b8;
}
.fix-stats {
  display: flex;
  gap: 12px;
}
.stat-card {
  min-width: 130px;
  background: #111827;
  border-color: #334155;
  text-align: center;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #f8fafc;
}
.stat-label {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 4px;
}
.fix-toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.fix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 16px;
}
.fix-card {
  background: #111827;
  border-color: #334155;
  cursor: pointer;
}
.fix-card.selected {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.18), 0 14px 32px rgba(120, 53, 15, 0.25);
}
.fix-detail-panel {
  background: #0f172a;
  border-color: #334155;
}
.detail-block {
  display: grid;
  gap: 10px;
}
.detail-block > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.detail-json {
  background: rgba(2, 6, 23, 0.65);
  border-radius: 12px;
  padding: 12px;
  max-height: 260px;
  overflow: auto;
}
.detail-json pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #cbd5e1;
  font-size: 12px;
}
.fix-card-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}
.fix-card-title {
  font-weight: 700;
  color: #f8fafc;
}
.fix-meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.severity-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  font-size: 12px;
  font-weight: 700;
}
.fix-summary {
  margin: 0 0 10px;
  color: #e2e8f0;
  line-height: 1.6;
}
.fix-detail {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
  background: rgba(2, 6, 23, 0.65);
  padding: 12px;
  border-radius: 12px;
  max-height: 190px;
  overflow: auto;
}
.fix-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid #334155;
}
.fix-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.sc-muted {
  color: #94a3b8;
  font-size: 12px;
}
.empty-state {
  color: #94a3b8;
  padding: 18px 4px;
}
@media (max-width: 1100px) {
  .fix-hero {
    flex-direction: column;
    align-items: start;
  }
}
</style>