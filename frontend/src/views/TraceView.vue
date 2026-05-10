<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { tracePayload, replayPayload, selectedTraceNode } = storeToRefs(store)

const traceNodes = computed(() => (tracePayload.value?.nodes as Array<Record<string, unknown>>) || [])
const replaySteps = computed(() => (replayPayload.value?.steps as Array<Record<string, unknown>>) || [])

const traceEventCount = computed(() => Number(tracePayload.value?.event_count ?? traceNodes.value.length))
const replayEventCount = computed(() => Number(replayPayload.value?.event_count ?? replaySteps.value.length))

const selectedNode = ref<Record<string, unknown> | null>(null)
const selectedStep = ref<Record<string, unknown> | null>(null)
const selectedNodeEl = ref<HTMLElement | null>(null)
const selectedStepEl = ref<HTMLElement | null>(null)

function openNode(node: Record<string, unknown>) {
  selectedNode.value = node
  selectedStep.value = null
  store.selectTraceNode(node)
}

function openStep(step: Record<string, unknown>) {
  selectedStep.value = step
  selectedNode.value = null
  store.selectTraceNode(step)
}

watch(selectedTraceNode, async (val) => {
  const nodeId = String(val?.id ?? val?.event_id ?? '')
  const stepIndex = String(val?.index ?? '')
  await nextTick()
  if (nodeId && selectedNode.value && String(selectedNode.value.id ?? '') === nodeId) {
    selectedNodeEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  if (stepIndex && selectedStep.value && String(selectedStep.value.index ?? '') === stepIndex) {
    selectedStepEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}, { immediate: true })
</script>

<template>
  <div class="trace-console">
    <div class="trace-hero">
      <div>
        <div class="eyebrow">ODD · Trace Console</div>
        <h2>执行链路可视化</h2>
        <p class="trace-subtitle">把执行过程、重放步骤、关键节点统一投影到一个可观察的控制台。</p>
      </div>
      <div class="trace-stats">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ traceEventCount }}</div>
          <div class="stat-label">Trace Events</div>
        </el-card>
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ replayEventCount }}</div>
          <div class="stat-label">Replay Steps</div>
        </el-card>
      </div>
    </div>

    <div class="trace-grid">
      <el-card shadow="never" class="trace-card trace-flow-card">
        <template #header>
          <div class="card-head">
            <span>Execution Flow</span>
            <span class="sc-muted">链路图</span>
          </div>
        </template>

        <div v-if="traceNodes.length === 0" class="empty-state">暂无 trace 节点</div>
        <div v-else class="flow-canvas">
          <div
            v-for="(node, idx) in traceNodes"
            :key="String(node.id)"
            ref="selectedNodeEl"
            class="flow-node"
            :class="{ active: idx === traceNodes.length - 1, selected: selectedNode && selectedNode.id === node.id }"
            @click="openNode(node)"
          >
            <div class="flow-node-top">
              <span class="flow-index">{{ idx + 1 }}</span>
              <span class="flow-label">{{ node.label }}</span>
            </div>
            <div class="flow-node-id">{{ node.id }}</div>
            <pre class="flow-node-data">{{ JSON.stringify(node.event, null, 2) }}</pre>
          </div>
        </div>
      </el-card>

      <div class="trace-side">
        <el-card shadow="never" class="trace-card">
          <template #header>
            <div class="card-head">
              <span>Replay Timeline</span>
              <span class="sc-muted">步骤面板</span>
            </div>
          </template>

          <div v-if="replaySteps.length === 0" class="empty-state">暂无 replay 步骤</div>
          <div v-else class="step-list">
            <div v-for="step in replaySteps" :key="String(step.index)" ref="selectedStepEl" class="step-card" :class="{ selected: selectedStep && selectedStep.index === step.index }" @click="openStep(step)">
              <div class="step-meta">
                <span class="step-index">#{{ step.index }}</span>
                <span class="step-kind">{{ step.kind }}</span>
              </div>
              <pre class="step-data">{{ JSON.stringify(step.data, null, 2) }}</pre>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="trace-card">
          <template #header>
            <div class="card-head">
              <span>Current Snapshot</span>
              <span class="sc-muted">调试面板</span>
            </div>
          </template>

          <div class="snapshot-grid">
            <div class="snapshot-item">
              <span class="sc-muted">Run</span>
              <b>{{ String(tracePayload.run_id ?? replayPayload.run_id ?? '—') }}</b>
            </div>
            <div class="snapshot-item">
              <span class="sc-muted">Events</span>
              <b>{{ traceEventCount }}</b>
            </div>
            <div class="snapshot-item">
              <span class="sc-muted">Replay</span>
              <b>{{ replayEventCount }}</b>
            </div>
          </div>
        </el-card>

        <el-card v-if="selectedNode || selectedStep" shadow="never" class="trace-card detail-card">
          <template #header>
            <div class="card-head">
              <span>Selected Detail</span>
              <span class="sc-muted">节点详情</span>
            </div>
          </template>
          <template v-if="selectedNode">
            <div class="detail-title">{{ selectedNode.label }}</div>
            <div class="detail-meta">{{ selectedNode.id }}</div>
            <pre class="detail-data">{{ JSON.stringify(selectedNode.event, null, 2) }}</pre>
          </template>
          <template v-else-if="selectedStep">
            <div class="detail-title">Step #{{ selectedStep.index }}</div>
            <div class="detail-meta">{{ selectedStep.kind }}</div>
            <pre class="detail-data">{{ JSON.stringify(selectedStep.data, null, 2) }}</pre>
          </template>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trace-console {
  padding: 18px 20px 40px;
  display: grid;
  gap: 16px;
}
.trace-hero {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}
.eyebrow {
  color: #60a5fa;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
h2 {
  margin: 8px 0 6px;
  color: #f8fafc;
}
.trace-subtitle {
  margin: 0;
  color: #94a3b8;
}
.trace-stats {
  display: flex;
  gap: 12px;
}
.stat-card {
  min-width: 140px;
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
.trace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
  gap: 16px;
}
.trace-card {
  background: #111827;
  border-color: #334155;
}
.trace-flow-card {
  min-height: 720px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.sc-muted {
  color: #94a3b8;
  font-size: 12px;
}
.empty-state {
  color: #94a3b8;
  padding: 18px 4px;
}
.flow-canvas {
  display: grid;
  gap: 14px;
}
.flow-node {
  position: relative;
  padding: 14px 14px 12px;
  border: 1px solid #334155;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(17, 24, 39, 0.98));
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
  cursor: pointer;
}
.flow-node:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 24px;
  bottom: -15px;
  width: 2px;
  height: 15px;
  background: linear-gradient(180deg, #38bdf8, transparent);
}
.flow-node.active {
  border-color: #38bdf8;
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.15), 0 12px 30px rgba(8, 47, 73, 0.4);
}
.flow-node.selected {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.18), 0 14px 32px rgba(120, 53, 15, 0.35);
}
.flow-node-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.flow-index {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #0ea5e9;
  color: white;
  font-size: 12px;
  font-weight: 700;
}
.flow-label {
  color: #e2e8f0;
  font-weight: 600;
}
.flow-node-id {
  color: #93c5fd;
  font-size: 12px;
  margin-bottom: 10px;
}
.flow-node-data,
.step-data {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
  background: rgba(2, 6, 23, 0.65);
  padding: 12px;
  border-radius: 12px;
  max-height: 220px;
  overflow: auto;
}
.trace-side {
  display: grid;
  gap: 16px;
}
.step-list {
  display: grid;
  gap: 12px;
}
.step-card {
  padding: 12px;
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.55);
  cursor: pointer;
}
.step-card.selected {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.18);
}
.step-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.step-index {
  color: #38bdf8;
  font-weight: 700;
}
.step-kind {
  color: #e2e8f0;
  font-weight: 600;
}
.snapshot-grid {
  display: grid;
  gap: 12px;
}
.snapshot-item {
  padding: 12px;
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.detail-card {
  margin-top: 16px;
}
.detail-title {
  font-weight: 700;
  color: #f8fafc;
  margin-bottom: 4px;
}
.detail-meta {
  color: #93c5fd;
  font-size: 12px;
  margin-bottom: 10px;
}
.detail-data {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
  background: rgba(2, 6, 23, 0.65);
  padding: 12px;
  border-radius: 12px;
  max-height: 260px;
  overflow: auto;
}
@media (max-width: 1100px) {
  .trace-grid {
    grid-template-columns: 1fr;
  }
  .trace-hero {
    flex-direction: column;
    align-items: start;
  }
}
</style>
