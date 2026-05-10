<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { diagnoseScore, diagnoseTitle, diagnoseDesc, diagnoseIssues, deployPayload, promotionLog } = storeToRefs(store)

const score = computed(() => diagnoseScore.value ?? 0)
const fitnessSummary = computed(() => ({
  deployments: Array.isArray(deployPayload.value?.runtimes) ? deployPayload.value?.runtimes.length : 0,
  promoted: promotionLog.value.length,
}))
</script>

<template>
  <div class="fitness-wrap">
    <h2>Fitness</h2>
    <el-card shadow="never" class="fitness-card">
      <div class="fitness-score" :style="{ color: store.scoreColor(score) }">{{ score }}</div>
      <div class="fitness-title">{{ diagnoseTitle }}</div>
      <div class="fitness-desc">{{ diagnoseDesc }}</div>
      <div class="fitness-meta">
        <span>Deployments: {{ fitnessSummary.deployments }}</span>
        <span>Promoted: {{ fitnessSummary.promoted }}</span>
      </div>
    </el-card>
    <el-table :data="diagnoseIssues" stripe empty-text="暂无问题" class="fitness-table">
      <el-table-column prop="severity" label="Severity" width="120" />
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="detail" label="Detail" />
    </el-table>
  </div>
</template>
