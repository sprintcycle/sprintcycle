<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  apiConfigGet,
  apiConfigHistory,
  apiConfigImport,
  apiConfigPut,
  apiConfigReload,
} from './api'

const cfg = ref<Record<string, unknown>>({})
const orig = ref<Record<string, unknown>>({})
const busy = ref(false)
const history = ref<Record<string, unknown>[]>([])
const importInput = ref<HTMLInputElement | null>(null)

async function loadConfig() {
  busy.value = true
  try {
    const r = await apiConfigGet()
    const payload = r.data
    if (payload && typeof payload === 'object') {
      cfg.value = { ...payload }
      orig.value = { ...payload }
    }
    const h = await apiConfigHistory()
    if (Array.isArray(h.data)) {
      history.value = h.data as Record<string, unknown>[]
    }
  } catch (e) {
    ElMessage.error(String(e))
  } finally {
    busy.value = false
  }
}

async function saveConfig() {
  const updates: Record<string, unknown> = {}
  for (const k of Object.keys(cfg.value)) {
    if (JSON.stringify(cfg.value[k]) !== JSON.stringify(orig.value[k])) {
      updates[k] = cfg.value[k]
    }
  }
  if (updates.api_key === '***') {
    delete updates.api_key
  }
  if (!Object.keys(updates).length) {
    ElMessage.info('无变更')
    return
  }
  busy.value = true
  try {
    const r = await apiConfigPut({ updates })
    if (r.success === false) {
      ElMessage.error(typeof r.error === 'string' ? r.error : '保存失败')
      return
    }
    ElMessage.success('已保存到 sprintcycle.runtime.yaml')
    await loadConfig()
  } catch (e) {
    if (axios.isAxiosError(e) && e.response?.data) {
      const d = e.response.data as { detail?: unknown }
      ElMessage.error(typeof d.detail === 'string' ? d.detail : JSON.stringify(d.detail ?? e.message))
    } else {
      ElMessage.error(String(e))
    }
  } finally {
    busy.value = false
  }
}

async function doReload() {
  busy.value = true
  try {
    await apiConfigReload()
    ElMessage.success('已从磁盘重新加载')
    await loadConfig()
  } catch (e) {
    ElMessage.error(String(e))
  } finally {
    busy.value = false
  }
}

function exportJson() {
  const blob = new Blob([JSON.stringify(cfg.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'sprintcycle-config-export.json'
  a.click()
  URL.revokeObjectURL(url)
}

function triggerImport() {
  importInput.value?.click()
}

function onImportFile(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async () => {
    try {
      const text = String(reader.result ?? '')
      const parsed = JSON.parse(text) as Record<string, unknown>
      if (!parsed || typeof parsed !== 'object') throw new Error('无效 JSON')
      busy.value = true
      const r = await apiConfigImport(parsed)
      if (r.success === false) {
        ElMessage.error(typeof r.error === 'string' ? r.error : '导入失败')
        return
      }
      ElMessage.success('已导入并持久化')
      await loadConfig()
    } catch (e) {
      ElMessage.error(String(e))
    } finally {
      busy.value = false
      input.value = ''
    }
  }
  reader.readAsText(file)
}

defineExpose({ load: loadConfig })
</script>

<template>
  <div class="cfg-wrap">
    <div class="cfg-toolbar">
      <span class="sc-muted">合并：<code>sprintcycle.toml</code> → <code>sprintcycle.runtime.yaml</code> → <code>SPRINTCYCLE_*</code></span>
      <div class="cfg-actions">
        <el-button size="small" :loading="busy" @click="loadConfig">🔄 刷新</el-button>
        <el-button size="small" :loading="busy" @click="doReload">♻ Reload</el-button>
        <el-button size="small" @click="exportJson">⬇ 导出 JSON</el-button>
        <input ref="importInput" type="file" accept="application/json,.json" class="visually-hidden" @change="onImportFile" />
        <el-button size="small" @click="triggerImport">⬆ 导入 JSON</el-button>
        <el-button type="primary" size="small" :loading="busy" @click="saveConfig">💾 保存</el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      class="cfg-alert"
      title="敏感项"
      description="api_key 展示为 *** 时不写入变更；需更新密钥请直接输入新值后保存。"
    />

    <el-tabs type="border-card" class="cfg-tabs">
      <el-tab-pane label="项目 / 执行">
        <el-form label-width="160px" class="cfg-form">
          <el-form-item label="project_path">
            <el-input v-model="cfg.project_path as string" />
          </el-form-item>
          <el-form-item label="parallel_tasks">
            <el-input-number v-model="cfg.parallel_tasks as number" :min="1" :max="32" />
          </el-form-item>
          <el-form-item label="max_sprints">
            <el-input-number v-model="cfg.max_sprints as number" :min="1" :max="500" />
          </el-form-item>
          <el-form-item label="max_tasks_per_sprint">
            <el-input-number v-model="cfg.max_tasks_per_sprint as number" :min="1" :max="200" />
          </el-form-item>
          <el-form-item label="continue_on_error">
            <el-switch v-model="cfg.continue_on_error as boolean" />
          </el-form-item>
          <el-form-item label="dry_run">
            <el-switch v-model="cfg.dry_run as boolean" />
          </el-form-item>
          <el-form-item label="max_verify_fix_rounds">
            <el-input-number v-model="cfg.max_verify_fix_rounds as number" :min="0" :max="20" />
          </el-form-item>
          <el-form-item label="coding_engine">
            <el-input v-model="cfg.coding_engine as string" placeholder="aider | litellm | …" />
          </el-form-item>
          <el-form-item label="execution_event_backend">
            <el-select v-model="cfg.execution_event_backend as string" style="width: 220px">
              <el-option label="sqlite" value="sqlite" />
              <el-option label="memory" value="memory" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="质量 / LLM">
        <el-form label-width="160px" class="cfg-form">
          <el-form-item label="quality_level">
            <el-input v-model="cfg.quality_level as string" placeholder="L0–L3" />
          </el-form-item>
          <el-form-item label="quality_profile">
            <el-input v-model="cfg.quality_profile as string" placeholder="default | strict | …" />
          </el-form-item>
          <el-form-item label="min_coverage_percent">
            <el-input-number v-model="cfg.min_coverage_percent as number" :min="0" :max="100" :step="1" />
          </el-form-item>
          <el-form-item label="llm_provider">
            <el-input v-model="cfg.llm_provider as string" />
          </el-form-item>
          <el-form-item label="llm_model">
            <el-input v-model="cfg.llm_model as string" />
          </el-form-item>
          <el-form-item label="llm_temperature">
            <el-input-number v-model="cfg.llm_temperature as number" :min="0" :max="2" :step="0.05" />
          </el-form-item>
          <el-form-item label="llm_max_tokens">
            <el-input-number v-model="cfg.llm_max_tokens as number" :min="256" :max="128000" :step="256" />
          </el-form-item>
          <el-form-item label="api_base">
            <el-input v-model="cfg.api_base as string" placeholder="可选" />
          </el-form-item>
          <el-form-item label="api_key">
            <el-input v-model="cfg.api_key as string" type="password" show-password autocomplete="off" />
          </el-form-item>
          <el-form-item label="api_timeout">
            <el-input-number v-model="cfg.api_timeout as number" :min="5" :max="3600" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="存储 / 缓存 / HITL / 治理">
        <el-form label-width="180px" class="cfg-form">
          <el-form-item label="storage_backend">
            <el-select v-model="cfg.storage_backend as string" style="width: 200px">
              <el-option label="sqlite" value="sqlite" />
              <el-option label="json" value="json" />
            </el-select>
          </el-form-item>
          <el-form-item label="state_dir">
            <el-input v-model="cfg.state_dir as string" />
          </el-form-item>
          <el-form-item label="cache_enabled">
            <el-switch v-model="cfg.cache_enabled as boolean" />
          </el-form-item>
          <el-form-item label="cache_backend">
            <el-select v-model="cfg.cache_backend as string" style="width: 200px">
              <el-option label="diskcache" value="diskcache" />
              <el-option label="redis" value="redis" />
            </el-select>
          </el-form-item>
          <el-form-item label="cache_dir">
            <el-input v-model="cfg.cache_dir as string" />
          </el-form-item>
          <el-form-item label="hitl_enabled">
            <el-switch v-model="cfg.hitl_enabled as boolean" />
          </el-form-item>
          <el-form-item label="hitl_default_timeout_seconds">
            <el-input-number v-model="cfg.hitl_default_timeout_seconds as number" :min="1" :max="86400" />
          </el-form-item>
          <el-form-item label="governance_enabled">
            <el-switch v-model="cfg.governance_enabled as boolean" />
          </el-form-item>
          <el-form-item label="governance_block_on">
            <el-select v-model="cfg.governance_block_on as string" style="width: 260px">
              <el-option label="none" value="none" />
              <el-option label="review_only" value="review_only" />
              <el-option label="planning_and_review" value="planning_and_review" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="变更历史">
        <div v-if="history.length === 0" class="sc-muted">暂无记录</div>
        <el-table v-else :data="history" size="small" stripe max-height="360">
          <el-table-column prop="ts" label="时间" width="200" />
          <el-table-column prop="source" label="来源" width="120" />
          <el-table-column prop="keys" label="键">
            <template #default="{ row }">
              {{ Array.isArray(row.keys) ? row.keys.join(', ') : row.keys }}
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="备注" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.cfg-wrap {
  padding: 0 0 1rem;
}
.cfg-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.cfg-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.cfg-alert {
  margin-bottom: 12px;
}
.cfg-tabs {
  background: #1e293b;
  border-color: #334155;
}
.cfg-form {
  max-width: 720px;
  padding: 8px 0;
}
.visually-hidden {
  position: fixed;
  left: -9999px;
  width: 1px;
  height: 1px;
  opacity: 0;
}
</style>
