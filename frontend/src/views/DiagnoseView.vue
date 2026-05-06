<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { diagnoseLoading, diagnoseScore, diagnoseTitle, diagnoseDesc, diagnoseIssues, diagnoseStats } =
  storeToRefs(store)

function issueText(issue: Record<string, unknown>) {
  return String(issue.message ?? issue.msg ?? JSON.stringify(issue))
}
</script>

<template>
  <div class="diag">
    <el-row :gutter="20" align="middle">
      <el-col :span="8" :xs="24">
        <div v-if="diagnoseScore != null" class="score-ring">
          <el-progress type="dashboard" :percentage="diagnoseScore" :color="store.scoreColor(diagnoseScore)" />
          <div class="score-num" :style="{ color: store.scoreColor(diagnoseScore) }">
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
            <span class="item-ico">{{ store.issueIcon(String(issue.severity ?? 'info').toLowerCase()) }}</span>
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
