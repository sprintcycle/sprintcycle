import { createRouter, createWebHistory } from 'vue-router'

import DashboardLayout from '@/layouts/DashboardLayout.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DashboardLayout,
      redirect: { name: 'overview' },
      children: [
        { path: 'overview', name: 'overview', component: () => import('@/views/OverviewView.vue') },
        { path: 'platform', name: 'platform', component: () => import('@/views/PlatformView.vue') },
        { path: 'plan', name: 'plan', component: () => import('@/views/PlanView.vue') },
        { path: 'history', name: 'history', component: () => import('@/views/HistoryView.vue') },
        { path: 'hitl', name: 'hitl', component: () => import('@/views/HitlView.vue') },
        { path: 'diagnose', name: 'diagnose', component: () => import('@/views/DiagnoseView.vue') },
        { path: 'events', name: 'events', component: () => import('@/views/EventsView.vue') },
        { path: 'trace', name: 'trace', component: () => import('@/views/TraceView.vue') },
        { path: 'governance', name: 'governance', component: () => import('@/views/GovernanceView.vue') },
        { path: 'fix', name: 'fix', component: () => import('@/views/FixView.vue') },
        { path: 'promotion', name: 'promotion', component: () => import('@/views/PromotionView.vue') },
        { path: 'deploy', name: 'deploy', component: () => import('@/views/DeployView.vue') },
        { path: 'fitness', name: 'fitness', component: () => import('@/views/FitnessView.vue') },
      ],
    },
  ],
})
