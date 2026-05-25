<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useExecutionStore } from '@/stores'

const store = useExecutionStore()
const { diagnoseLoading, diagnoseResult } = storeToRefs(store)

const diagnoseScore = computed(() => diagnoseResult.value?.health_score ?? null)
const diagnoseIssues = computed(() => diagnoseResult.value?.issues ?? [])
const diagnoseStats = computed(() => {
  let pass = 0
  let warn = 0
  let fail = 0
  for (const i of diagnoseIssues.value) {
    const sev = String(i.severity ?? 'info').toLowerCase()
    if (['pass', 'ok', 'info'].includes(sev)) pass += 1
    else if (['warn', 'warning'].includes(sev)) warn += 1
    else if (['fail', 'error', 'critical'].includes(sev)) fail += 1
  }
  return { pass, warn, fail }
})

const diagnoseTitle = computed(() => {
  if (diagnoseScore.value === null) return '项目诊断'
  if (diagnoseScore.value >= 80) return '✅ 项目健康'
  if (diagnoseScore.value >= 50) return '⚠ 项目需要注意'
  return '🚨 项目需要修复'
})

const diagnoseDesc = computed(() => {
  if (diagnoseScore.value === null) return '点击下方按钮检查项目健康状态'
  if (diagnoseScore.value >= 80) return `健康分 ${diagnoseScore.value}/100，共 ${diagnoseIssues.value.length} 项检查`
  if (diagnoseScore.value >= 50) return `健康分 ${diagnoseScore.value}/100，失败 ${diagnoseStats.value.fail} / 警告 ${diagnoseStats.value.warn}`
  return `健康分 ${diagnoseScore.value}/100，存在 ${diagnoseStats.value.fail} 个关键问题`
})

function scoreColor(score: number) {
  if (score >= 80) return '#22c55e'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

function issueIcon(sev: string) {
  if (['pass', 'ok'].includes(sev)) return '✅'
  if (['warn', 'warning'].includes(sev)) return '⚠️'
  if (['fail', 'error', 'critical'].includes(sev)) return '❌'
  return 'ℹ️'
}

function issueText(issue: Record<string, unknown>) {
  return String(issue.message ?? issue.msg ?? issue.description ?? JSON.stringify(issue))
}
</script>

<template>
  <div class="diag">
    <el-row :gutter="20" align="middle">
      <el-col :span="8" :xs="24">
        <div v-if="diagnoseScore != null" class="score-ring">
          <el-progress type="dashboard" :percentage="diagnoseScore" :color="scoreColor(diagnoseScore)" />
          <div class="score-num" :style="{ color: scoreColor(diagnoseScore) }">
            {{ diagnoseScore }}
          </div>
          <div class="sc-muted">健康分</div>
        </div>
        <div v-else class="sc-muted">尚未诊断</div>
      </el-col>
      <el-col :span="16" :xs="24">
        <h2>{{ diagnoseTitle }}</h2>
        <p class="sc-muted">{{ diagnoseDesc }}</p>
        <el-button :loading="diagnoseLoading" type="primary" @click="store.runDiagnose">
          🏥 开始诊断
        </el-button>
        <div v-if="diagnoseIssues.length" class="diag-counts">
          <span class="ok">通过 {{ diagnoseStats.pass }}</span>
          <span class="warn">警告 {{ diagnoseStats.warn }}</span>
          <span class="fail">失败 {{ diagnoseStats.fail }}</span>
        </div>
      </el-col>
    </el-row>
    <h3 class="section-title">检查项</h3>
    <el-row :gutter="12">
      <el-col v-for="(issue, ii) in diagnoseIssues" :key="ii" :span="12" :xs="24">
        <el-card shadow="never" class="diag-item">
          <div class="item-row">
            <span class="item-ico">{{ issueIcon(String(issue.severity ?? 'info').toLowerCase()) }}</span>
            <div>
              <div class="item-sev">{{ String(issue.severity ?? 'INFO').toUpperCase() }}</div>
              <div class="item-msg">{{ issueText(issue as Record<string, unknown>) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <div v-if="diagnoseIssues.length === 0 && diagnoseScore != null" class="sc-muted">
      暂无详细检查项
    </div>
  </div>
</template>
