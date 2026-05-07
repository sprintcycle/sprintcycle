<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { apiGovernanceCheck, apiGovernanceHistory, apiGovernanceLatest } from '@/api'

const loading = ref(false)
const running = ref(false)
const gate = ref<'review' | 'planning' | 'both'>('review')
const latest = ref<Record<string, unknown> | null>(null)
const historyEntries = ref<Record<string, unknown>[]>([])

async function refresh() {
  loading.value = true
  try {
    latest.value = (await apiGovernanceLatest()) as Record<string, unknown>
  } catch {
    latest.value = null
  }
  try {
    const h = await apiGovernanceHistory(50)
    historyEntries.value = Array.isArray(h.entries) ? (h.entries as Record<string, unknown>[]) : []
  } catch {
    historyEntries.value = []
  }
  loading.value = false
}

async function runCheck() {
  running.value = true
  try {
    const res = await apiGovernanceCheck(gate.value)
    ElMessage.success(
      res.should_fail_ci ? '门禁完成（存在 error，见 should_fail_ci）' : '门禁完成',
    )
    await refresh()
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '请求失败')
  }
  running.value = false
}

onMounted(() => {
  void refresh()
})
</script>

<template>
  <div class="gov">
    <h2>治理与多源验证</h2>
    <p class="sc-muted">
      与 CLI
      <code>sprintcycle governance check</code> / <code>sprintcycle validate</code>
      对齐；详见仓库
      <code>docs/GOVERNANCE_HEAVY_CHECKS.md</code>。
    </p>

    <el-card shadow="never" class="gov-card">
      <template #header>
        <span>运行门禁</span>
      </template>
      <el-space wrap>
        <el-select v-model="gate" style="width: 160px">
          <el-option label="Review" value="review" />
          <el-option label="Planning" value="planning" />
          <el-option label="Both" value="both" />
        </el-select>
        <el-button type="primary" :loading="running" @click="runCheck">执行检查</el-button>
        <el-button :loading="loading" @click="refresh">刷新最新 / 历史</el-button>
      </el-space>
      <p class="sc-muted hint">
        排障：在终端执行
        <code>sprintcycle validate --gate review</code>
        ；实时事件见「实时事件」页（<code>GOVERNANCE_GATE</code>）。
      </p>
    </el-card>

    <el-card v-if="latest" shadow="never" class="gov-card">
      <template #header>最近一次落盘报告</template>
      <el-tabs>
        <el-tab-pane v-if="latest.planning" label="Planning" lazy>
          <pre class="json">{{ JSON.stringify(latest.planning, null, 2) }}</pre>
        </el-tab-pane>
        <el-tab-pane v-if="latest.review" label="Review" lazy>
          <pre class="json">{{ JSON.stringify(latest.review, null, 2) }}</pre>
        </el-tab-pane>
      </el-tabs>
      <p v-if="!latest.planning && !latest.review" class="sc-muted">无 planning/review 字段</p>
    </el-card>
    <el-card v-else shadow="never" class="gov-card">
      <p class="sc-muted">尚无落盘报告（先执行检查或跑 Sprint 门禁）。</p>
    </el-card>

    <el-card shadow="never" class="gov-card">
      <template #header>历史快照（趋势）</template>
      <el-table v-loading="loading" :data="historyEntries" empty-text="暂无历史" stripe>
        <el-table-column prop="written_at" label="时间(UTC)" width="180" />
        <el-table-column prop="gate" label="门" width="100" />
        <el-table-column prop="error_count" label="Errors" width="90" />
        <el-table-column prop="warning_count" label="Warnings" width="100" />
        <el-table-column prop="violation_count" label="Violations" width="110" />
        <el-table-column prop="file" label="文件" min-width="200" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.gov {
  padding: 16px 20px 40px;
  max-width: 1200px;
}
.gov-card {
  margin-bottom: 16px;
  background: #1e293b;
  border-color: #334155;
}
.sc-muted {
  color: #94a3b8;
  font-size: 13px;
}
.hint {
  margin-top: 12px;
}
.json {
  max-height: 420px;
  overflow: auto;
  font-size: 12px;
  background: #0f172a;
  padding: 12px;
  border-radius: 8px;
  color: #e2e8f0;
}
h2 {
  margin-top: 0;
  color: #f1f5f9;
}
</style>
