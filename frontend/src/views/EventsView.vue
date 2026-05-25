<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useEventsStore } from '@/stores/events'

const store = useEventsStore()
const { eventLines, autoScroll, eventsLogRef } = storeToRefs(store)
</script>

<template>
  <div class="events-wrap">
    <div class="events-toolbar">
      <span class="sc-muted">实时事件流 (SSE)</span>
      <el-checkbox v-model="autoScroll">自动滚动</el-checkbox>
      <el-button size="small" @click="store.clearEvents">🗑️ 清除</el-button>
    </div>
    <div ref="eventsLogRef" class="events-log">
      <div v-for="(row, ri) in eventLines" :key="ri" class="event-line" :class="'t-' + row.type">
        <span class="ev-ts">{{ row.ts }}</span>
        <span class="ev-type">{{ row.display }}</span>
        <span class="ev-msg">{{ row.text }}</span>
        <el-tag v-if="row.agent" size="small" type="info" effect="dark">{{ row.agent }}</el-tag>
      </div>
    </div>
  </div>
</template>