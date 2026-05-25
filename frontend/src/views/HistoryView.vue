<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'

import { useExecutionStore } from '@/stores/execution'

const store = useExecutionStore()
const { executions, loaded, expanded } = storeToRefs(store)

function shortId(id: string): string {
  return id.slice(0, 8)
}

function canResume(ex: Record<string, unknown>): boolean {
  return String(ex.status) === 'paused' || String(ex.status) === 'interrupted'
}

function finalizationForExec(ex: Record<string, unknown>): Record<string, unknown> {
  return {}
}

function sprintRows(ex: Record<string, unknown>): Record<string, unknown>[] {
  return []
}

function taskRows(sp: Record<string, unknown>): (string | Record<string, unknown>)[] {
  return []
}

const selectedId = ref<string>('')

function toggleExpand(id: string) {
  selectedId.value = selectedId.value === id ? '' : id
}

onMounted(() => void store.loadHistory())
</script>

<template>
  <div class="sc-history">
    <div class="sc-history-toolbar">
      <span class="sc-muted">近期执行记录</span>
      <el-button size="small" @click="store.loadHistory">🔄 刷新</el-button>
    </div>
    <div v-if="!loaded" class="sc-muted">加载中...</div>
    <div v-else-if="executions.length === 0" class="sc-empty">
      📭 暂无执行历史
    </div>
    <div v-else class="exec-list">
      <el-card v-for="ex in executions" :key="String(ex.execution_id)" class="exec-card" shadow="hover">
        <div class="exec-row" @click="toggleExpand(String(ex.execution_id ?? ''))">
          <span class="exec-short">{{ shortId(String(ex.execution_id ?? '')) }}</span>
          <el-tag size="small" effect="dark">{{ String(ex.status ?? 'unknown') }}</el-tag>
          <div class="exec-meta">
            <span v-if="ex.release_plan_name">📦 {{ ex.release_plan_name }}</span>
            <span v-if="ex.mode">⚙ {{ ex.mode }}</span>
            <span v-if="Number(ex.total_sprints) > 0">
              Sprint {{ ex.current_sprint ?? 0 }}/{{ ex.total_sprints }}
            </span>
            <span v-if="ex.completed_tasks != null">
              📋 {{ ex.completed_tasks }}/{{ ex.total_tasks ?? '?' }} 任务
            </span>
            <span v-if="ex.created_at">🕐 {{ new Date(String(ex.created_at)).toLocaleString('zh-CN') }}</span>
            <span v-if="ex.error" class="err">❌ {{ String(ex.error).slice(0, 80) }}</span>
          </div>
          <div class="exec-actions">
            <el-button
v-if="canResume(ex)" type="success" size="small"
              @click.stop="store.resume(String(ex.execution_id))">
              ▶ Resume
            </el-button>
            <el-button
type="warning" size="small" plain
              @click.stop="store.rollback(String(ex.execution_id ?? ''))">
              ↩ 回滚
            </el-button>
            <el-button size="small" @click.stop="store.stop(String(ex.execution_id ?? ''))">⏹</el-button>
          </div>
          <span class="chev" :class="{ open: selectedId === String(ex.execution_id) }">▶</span>
        </div>
        <div v-show="selectedId === String(ex.execution_id)" class="exec-detail">
          <div class="finalization-card" v-if="finalizationForExec(ex) && Object.keys(finalizationForExec(ex)).length">
            <div class="sprint-head">
              <span class="sprint-dot success" />
              <b>Release Finalization</b>
              <span class="sc-muted">
                {{ String((finalizationForExec(ex) as Record<string, unknown>).summary ?? '') }}
              </span>
              <span class="sc-muted">
                ready: {{ String((finalizationForExec(ex) as Record<string, unknown>).ready_to_release ?? false) }}
              </span>
            </div>
            <div class="task-row" v-if="Array.isArray((finalizationForExec(ex) as Record<string, unknown>).issues) && (finalizationForExec(ex) as Record<string, unknown>).issues.length">
              <span class="sc-muted">Issues</span>
              <span>{{ (finalizationForExec(ex) as Record<string, unknown>).issues.join(' · ') }}</span>
            </div>
            <div class="task-row" v-if="Array.isArray((finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints) && (finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints.length">
              <span class="sc-muted">Fix Sprints</span>
              <span>{{ (finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints.length }}</span>
            </div>
          </div>
          <div v-if="sprintRows(ex).length === 0" class="sc-muted pad">暂无详细信息</div>
          <div v-else class="sprint-section">
            <div v-for="(sp, si) in sprintRows(ex)" :key="si" class="sprint-card">
              <div class="sprint-head">
                <span class="sprint-dot" :class="String((sp as Record<string, unknown>).status ?? '')" />
                <b>{{ String((sp as Record<string, unknown>).sprint_name ?? (sp as Record<string, unknown>).name ?? `Sprint ${si + 1}`) }}</b>
                <span class="sc-muted">{{ String((sp as Record<string, unknown>).status ?? '') }}</span>
                <span v-if="typeof (sp as Record<string, unknown>).duration === 'number'" class="sc-muted">
                  ⏱ {{ Number((sp as Record<string, unknown>).duration).toFixed(1) }}s
                </span>
              </div>
              <div v-for="(t, ti) in taskRows(sp as Record<string, unknown>)" :key="ti" class="task-row">
                <template v-if="typeof t === 'string'">
                  {{ t }}
                </template>
                <template v-else-if="t && typeof t === 'object'">
                  <span :class="'ic-' + String((t as Record<string, unknown>).status ?? '')">
                    {{ (t as Record<string, unknown>).status === 'failed' ? '❌' : (t as Record<string, unknown>).status === 'success' ? '✅' : '⏳' }}
                  </span>
                  <span>{{ String((t as Record<string, unknown>).description ?? '') }}</span>
                  <span class="sc-muted agent">{{ String((t as Record<string, unknown>).agent ?? '') }}</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>