<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { hitlPending, hitlHistory, hitlNotes, hitlBusy } = storeToRefs(store)
</script>

<template>
  <div class="hitl-wrap">
    <div class="sc-history-toolbar">
      <span class="sc-muted">待决策与近期历史（SSE 可实时刷新列表）</span>
      <el-button size="small" :loading="hitlBusy" @click="store.loadHitl">🔄 刷新</el-button>
    </div>
    <h3 class="section-title">待处理</h3>
    <div v-if="hitlPending.length === 0" class="sc-muted pad">暂无待处理请求（未启用 HITL 或无运行中卡点）</div>
    <template v-else>
      <el-card v-for="req in hitlPending" :key="String(req.request_id)" shadow="hover" class="hitl-card">
        <template #header>
          <div class="hitl-head">
            <b>{{ String(req.title ?? '') }}</b>
            <el-tag size="small" type="warning">{{ String(req.gate ?? '') }}</el-tag>
          </div>
        </template>
        <p class="sc-muted">{{ String(req.summary ?? '') }}</p>
        <p class="sc-muted small">exec {{ store.shortId(String(req.execution_id ?? '')) }} · {{ String(req.request_id ?? '').slice(0, 12) }}…</p>
        <el-input
v-model="hitlNotes[String(req.request_id)]" type="textarea" :rows="2" placeholder="备注（可选）"
          class="hitl-note" />
        <div class="hitl-actions">
          <el-button type="success" size="small" @click="store.submitHitlDecision(String(req.request_id), 'approve')">
            批准
          </el-button>
          <el-button type="info" size="small" @click="store.submitHitlDecision(String(req.request_id), 'skip_sprint')">
            跳过 Sprint
          </el-button>
          <el-button
type="danger" size="small"
            @click="store.submitHitlDecision(String(req.request_id), 'abort_execution')">
            中止执行
          </el-button>
        </div>
      </el-card>
    </template>
    <h3 class="section-title">近期历史</h3>
    <div v-if="hitlHistory.length === 0" class="sc-muted pad">暂无</div>
    <el-table v-else :data="hitlHistory" size="small" stripe class="hitl-table">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="gate" label="门" width="120" />
      <el-table-column prop="decision" label="决策" width="140" />
      <el-table-column prop="title" label="标题" />
    </el-table>
  </div>
</template>
