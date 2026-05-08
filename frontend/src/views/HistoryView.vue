<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { executions, historyLoaded, expanded } = storeToRefs(store)
</script>

<template>
  <div class="sc-history">
    <div class="sc-history-toolbar">
      <span class="sc-muted">近期执行记录</span>
      <el-button size="small" @click="store.loadHistory">🔄 刷新</el-button>
    </div>
    <div v-if="!historyLoaded" class="sc-muted">加载中...</div>
    <div v-else-if="executions.length === 0" class="sc-empty">
      📭 暂无执行历史
    </div>
    <div v-else class="exec-list">
      <el-card v-for="ex in executions" :key="String(ex.execution_id)" class="exec-card" shadow="hover">
        <div class="exec-row" @click="store.toggleExpand(String(ex.execution_id ?? ''))">
          <span class="exec-short">{{ store.shortId(String(ex.execution_id ?? '')) }}</span>
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
v-if="store.canResume(ex)" type="success" size="small"
              @click.stop="store.handleResume(String(ex.execution_id))">
              ▶ Resume
            </el-button>
            <el-button
type="warning" size="small" plain
              @click.stop="store.handleRollback(String(ex.execution_id ?? ''))">
              ↩ 回滚
            </el-button>
            <el-button size="small" @click.stop="store.handleStop(String(ex.execution_id ?? ''))">⏹</el-button>
          </div>
          <span class="chev" :class="{ open: expanded[String(ex.execution_id)] }">▶</span>
        </div>
        <div v-show="expanded[String(ex.execution_id)]" class="exec-detail">
          <div class="finalization-card" v-if="store.finalizationForExec(ex) && Object.keys(store.finalizationForExec(ex)).length">
            <div class="sprint-head">
              <span class="sprint-dot success" />
              <b>Release Finalization</b>
              <span class="sc-muted">
                {{ String((store.finalizationForExec(ex) as Record<string, unknown>).summary ?? '') }}
              </span>
              <span class="sc-muted">
                ready: {{ String((store.finalizationForExec(ex) as Record<string, unknown>).ready_to_release ?? false) }}
              </span>
            </div>
            <div class="task-row" v-if="Array.isArray((store.finalizationForExec(ex) as Record<string, unknown>).issues) && (store.finalizationForExec(ex) as Record<string, unknown>).issues.length">
              <span class="sc-muted">Issues</span>
              <span>{{ (store.finalizationForExec(ex) as Record<string, unknown>).issues.join(' · ') }}</span>
            </div>
            <div class="task-row" v-if="Array.isArray((store.finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints) && (store.finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints.length">
              <span class="sc-muted">Fix Sprints</span>
              <span>{{ (store.finalizationForExec(ex) as Record<string, unknown>).executed_fix_sprints.length }}</span>
            </div>
          </div>
          <div v-if="store.sprintRows(ex).length === 0" class="sc-muted pad">暂无详细信息</div>
          <div v-else class="sprint-section">
            <div v-for="(sp, si) in store.sprintRows(ex)" :key="si" class="sprint-card">
              <div class="sprint-head">
                <span class="sprint-dot" :class="String((sp as Record<string, unknown>).status ?? '')" />
                <b>{{ String((sp as Record<string, unknown>).sprint_name ?? (sp as Record<string, unknown>).name ?? `Sprint ${si + 1}`) }}</b>
                <span class="sc-muted">{{ String((sp as Record<string, unknown>).status ?? '') }}</span>
                <span v-if="typeof (sp as Record<string, unknown>).duration === 'number'" class="sc-muted">
                  ⏱ {{ Number((sp as Record<string, unknown>).duration).toFixed(1) }}s
                </span>
              </div>
              <div v-for="(t, ti) in store.taskRows(sp as Record<string, unknown>)" :key="ti" class="task-row">
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
