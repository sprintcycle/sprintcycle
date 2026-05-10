<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { deployPayload } = storeToRefs(store)

const runtimes = computed(() => (deployPayload.value?.runtimes as Array<Record<string, unknown>>) || [])
</script>

<template>
  <div class="deploy-wrap">
    <h2>Deployment Status</h2>
    <el-table :data="runtimes" stripe empty-text="暂无部署记录">
      <el-table-column prop="runtime_id" label="Runtime ID" width="180" />
      <el-table-column prop="project_name" label="Project" />
      <el-table-column prop="status" label="Status" width="120" />
      <el-table-column prop="suggestion_id" label="Suggestion" width="180" />
      <el-table-column prop="evolution_id" label="Evolution" width="180" />
      <el-table-column prop="url" label="URL" />
    </el-table>
  </div>
</template>
