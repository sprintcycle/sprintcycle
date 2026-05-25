<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import { apiPlan, apiRun } from '@/api/execution'

const yamlInput = ref('')
const referencePathsText = ref('')
const writePolicy = ref('auto')
const planBusy = ref(false)
const planMeta = ref('')
const planMessage = ref('')
const planTone = ref('')

const policyOptions = [
  { label: 'auto（按目标是否存在）', value: 'auto' },
  { label: 'create（骨架/新建）', value: 'create' },
  { label: 'incremental（增量）', value: 'incremental' },
  { label: 'safe（只新增不改）', value: 'safe' },
]

function clearEditor() {
  yamlInput.value = ''
  planMessage.value = ''
  planMeta.value = ''
  planTone.value = ''
}

async function handlePlan() {
  if (!yamlInput.value.trim()) {
    ElMessage.warning('请输入执行计划')
    return
  }
  planBusy.value = true
  try {
    const result = await apiPlan({
      yaml: yamlInput.value,
      write_policy: writePolicy.value,
      reference_paths: referencePathsText.value.split('\n').filter(Boolean),
    })
    planMessage.value = result.message || JSON.stringify(result, null, 2)
    planMeta.value = result.meta || ''
    planTone.value = result.tone || 'info'
  } catch (e) {
    planMessage.value = e instanceof Error ? e.message : String(e)
    planTone.value = 'error'
  } finally {
    planBusy.value = false
  }
}

async function handleRun() {
  if (!yamlInput.value.trim()) {
    ElMessage.warning('请输入执行计划')
    return
  }
  planBusy.value = true
  try {
    const result = await apiRun({
      yaml: yamlInput.value,
      write_policy: writePolicy.value,
      reference_paths: referencePathsText.value.split('\n').filter(Boolean),
    })
    planMessage.value = result.message || JSON.stringify(result, null, 2)
    planMeta.value = result.meta || ''
    planTone.value = 'success'
    ElMessage.success('执行已启动')
  } catch (e) {
    planMessage.value = e instanceof Error ? e.message : String(e)
    planTone.value = 'error'
  } finally {
    planBusy.value = false
  }
}
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
          @keydown.ctrl.enter.prevent="handleRun" @keydown.meta.enter.prevent="handleRun" />
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
          <el-button @click="clearEditor">🗑️ 清空</el-button>
          <div class="grow" />
          <el-button :loading="planBusy" @click="handlePlan">📋 Plan</el-button>
          <el-button type="success" :loading="planBusy" @click="handleRun">
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