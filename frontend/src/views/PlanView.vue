<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { yamlInput, referencePathsText, writePolicy, planBusy, planMeta, planMessage, planTone } =
  storeToRefs(store)

const policyOptions = [
  { label: 'auto（按目标是否存在）', value: 'auto' },
  { label: 'create（骨架/新建）', value: 'create' },
  { label: 'incremental（增量）', value: 'incremental' },
  { label: 'safe（只新增不改）', value: 'safe' },
]
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
v-model="yamlInput" type="textarea" :rows="14" class="sc-yaml-input" placeholder="输入 YAML 或自然语言意图..."
          @keydown.ctrl.enter.prevent="store.handleRun" @keydown.meta.enter.prevent="store.handleRun" />
        <div class="sc-plan-extra">
          <el-select v-model="writePolicy" placeholder="写入策略" style="width: 100%" size="small">
            <el-option v-for="o in policyOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
          <el-input
            v-model="referencePathsText"
            type="textarea"
            :rows="3"
            size="small"
            class="sc-ref-paths"
            placeholder="参考项目路径（可选，一行一个；只读借鉴，写入仍在 Dashboard 绑定的项目根）"
          />
        </div>
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
