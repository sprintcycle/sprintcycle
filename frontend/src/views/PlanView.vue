<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { yamlInput, planBusy, planMeta, planMessage, planTone } = storeToRefs(store)
</script>

<template>
  <el-row :gutter="16" class="sc-plan-grid">
    <el-col :xs="24" :md="12">
      <el-card shadow="never" class="sc-card">
        <template #header>
          📝 执行计划 YAML
          <span class="sc-hint">支持自然语言或直接输入 YAML · Ctrl/Cmd+Enter 运行</span>
        </template>
        <el-input
v-model="yamlInput" type="textarea" :rows="18" class="sc-yaml-input" placeholder="输入 YAML 或自然语言意图..."
          @keydown.ctrl.enter.prevent="store.handleRun" @keydown.meta.enter.prevent="store.handleRun" />
        <div class="sc-card-actions">
          <el-button @click="store.clearEditor">🗑️ 清空</el-button>
          <div class="grow" />
          <el-button :loading="planBusy" @click="store.handlePlan">📋 Plan</el-button>
          <el-button type="success" :loading="planBusy" @click="store.handleRun">
            ▶ Run
          </el-button>
        </div>
      </el-card>
    </el-col>
    <el-col :xs="24" :md="12">
      <el-card shadow="never" class="sc-card">
        <template #header>
          📊 计划预览 <span class="sc-hint">{{ planMeta }}</span>
        </template>
        <div class="sc-plan-out" :class="[`tone-${planTone}`]">
          <pre class="pre">{{ planMessage }}</pre>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>
