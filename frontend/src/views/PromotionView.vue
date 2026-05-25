<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useSuggestionsStore } from '@/stores/suggestions'

const store = useSuggestionsStore()
const { promoted } = storeToRefs(store)
</script>

<template>
  <div class="promotion-wrap">
    <div class="promotion-head">
      <h2>Promoted Suggestions</h2>
      <span class="sc-muted">已批准并推进到演化请求的建议</span>
    </div>
    <div v-if="promoted.length === 0" class="sc-muted">暂无 promoted 记录</div>
    <el-card v-for="item in promoted" :key="String(item.suggestion_id ?? item.title ?? '')" shadow="never" class="promotion-card">
      <div class="promotion-title">{{ item.title }}</div>
      <div class="promotion-meta">{{ item.summary }}</div>
      <div class="promotion-meta">evolution: {{ item.linked_evolution_id || '—' }}</div>
      <div class="promotion-meta">status: {{ item.status }} · severity: {{ item.severity }}</div>
    </el-card>
  </div>
</template>