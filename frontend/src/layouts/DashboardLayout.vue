<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import { useDashboardStore } from '@/stores/dashboard'

const route = useRoute()
const store = useDashboardStore()
const { sseLabel, sseDotClass, clientCount, liveEventCount, historyBadge } = storeToRefs(store)

watch(
  () => route.name,
  (name) => store.onRouteChange(name),
  { immediate: true },
)

onMounted(() => store.mountDashboard())
onUnmounted(() => store.unmountDashboard())
</script>

<template>
  <div class="sc-app">
    <header class="sc-header">
      <div class="sc-logo">
        🚀 SprintCycle <span class="sc-logo-sub">控制台</span>
      </div>
      <div class="sc-header-right">
        <span class="sc-pill">
          <span class="dot" :class="sseDotClass" />
          <span>{{ sseLabel }}</span>
        </span>
        <span class="sc-pill">Clients: <b>{{ clientCount }}</b></span>
        <span class="sc-pill">Events: <b>{{ liveEventCount }}</b></span>
      </div>
    </header>

    <el-menu
mode="horizontal" router :default-active="route.path" class="sc-menu" background-color="#1e293b"
      text-color="#94a3b8" active-text-color="#38bdf8">
      <el-menu-item index="/overview">
        🏠 总览
      </el-menu-item>
      <el-menu-item index="/platform">
        📊 运行总览
      </el-menu-item>
      <el-menu-item index="/plan">
        📝 执行计划
      </el-menu-item>
      <el-menu-item index="/history">
        <span>📜 执行历史</span>
        <el-badge v-if="historyBadge > 0" :value="historyBadge" class="tab-badge" />
      </el-menu-item>
      <el-menu-item index="/hitl">
        ✋ 人机卡点
      </el-menu-item>
      <el-menu-item index="/diagnose">
        🏥 诊断
      </el-menu-item>
      <el-menu-item index="/events">
        <span>📡 实时事件</span>
        <el-badge :value="liveEventCount" class="tab-badge" />
      </el-menu-item>
      <el-menu-item index="/governance">
        ✅ 治理 / 多源验证
      </el-menu-item>
      <el-menu-item index="/trace">
        🔍 Trace
      </el-menu-item>
      <el-menu-item index="/fix">
        🛠 Fix
      </el-menu-item>
      <el-menu-item index="/promotion">
        📣 Promotion
      </el-menu-item>
      <el-menu-item index="/deploy">
        🚚 Deploy
      </el-menu-item>
      <el-menu-item index="/fitness">
        🧪 Fitness
      </el-menu-item>
    </el-menu>

    <div class="sc-main">
      <router-view />
    </div>
  </div>
</template>

<style>
html.dark body {
  background: #0f172a;
  margin: 0;
}
</style>

<style scoped>
.sc-app {
  min-height: 100vh;
  background: #0f172a;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
}

.sc-header {
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 20px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}

.sc-logo {
  font-weight: 700;
  font-size: 18px;
  color: #38bdf8;
}

.sc-logo-sub {
  font-weight: 400;
  font-size: 13px;
  color: #94a3b8;
  margin-left: 8px;
}

.sc-header-right {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.sc-pill {
  font-size: 12px;
  color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 20px;
  padding: 4px 12px;
  background: #0f172a;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
}

.dot.ok {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}

.dot.bad {
  background: #ef4444;
}

.dot.off {
  background: #64748b;
}

.sc-menu {
  border-bottom: 1px solid #334155 !important;
  flex-shrink: 0;
}

.sc-menu :deep(.el-menu-item) {
  border-bottom: none !important;
}

.tab-badge {
  margin-left: 6px;
  vertical-align: middle;
}

.sc-main {
  flex: 1;
  padding: 16px;
  min-height: 0;
}
</style>
