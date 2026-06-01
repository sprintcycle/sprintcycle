/**
 * SprintCycle 架构验证 E2E 测试
 * 
 * 基于 ARCHITECTURE_INVARIANTS.md 和架构约束规则
 * 自动化验证 Web 界面功能和流程
 */

import { expect, test } from '@playwright/test'

test.describe('架构不变性验证 - Web UI', () => {
  test('dashboard 主页面加载正常', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('SprintCycle', { exact: false }).first()).toBeVisible()
    await expect(page).toHaveTitle(/SprintCycle/)
  })

  test('导航菜单完整性', async ({ page }) => {
    await page.goto('/')
    
    const navItems = [
      '执行计划',
      '执行历史',
      '治理',
      'HITL',
      '建议',
      '平台'
    ]
    
    for (const item of navItems) {
      await expect(page.getByRole('menuitem', { name: new RegExp(item) })).toBeVisible()
    }
  })

  test('生命周期状态机流程验证', async ({ page }) => {
    await page.goto('/plan')
    
    // 验证计划页面结构
    await expect(page.getByRole('heading', { name: /执行计划/ })).toBeVisible()
    
    // 验证执行按钮存在
    await expect(page.getByRole('button', { name: /执行/ })).toBeEnabled()
  })

  test('治理页面功能验证', async ({ page }) => {
    await page.goto('/governance')
    
    // 验证治理页面结构
    await expect(page.getByRole('heading', { name: /治理/ })).toBeVisible()
    
    // 验证检查项存在
    await expect(page.getByText(/架构合规性/)).toBeVisible()
  })

  test('HITL 页面验证', async ({ page }) => {
    await page.goto('/hitl')
    
    // 验证 HITL 页面结构
    await expect(page.getByRole('heading', { name: /HITL/ })).toBeVisible()
  })

  test('历史记录页面验证', async ({ page }) => {
    await page.goto('/history')
    
    // 验证历史记录页面结构
    await expect(page.getByText('近期执行记录')).toBeVisible()
  })

  test('页面路由切换正常', async ({ page }) => {
    await page.goto('/')
    
    const routes = [
      { path: '/plan', expectedText: '执行计划' },
      { path: '/history', expectedText: '近期执行记录' },
      { path: '/governance', expectedText: '治理' },
      { path: '/hitl', expectedText: 'HITL' },
    ]
    
    for (const route of routes) {
      await page.getByRole('menuitem', { name: new RegExp(route.expectedText) }).click()
      await expect(page.url()).toContain(route.path)
      await expect(page.getByText(route.expectedText)).toBeVisible()
    }
  })

  test('响应式布局验证', async ({ page }) => {
    await page.goto('/')
    
    // 测试桌面端布局
    await page.setViewportSize({ width: 1280, height: 800 })
    await expect(page.getByRole('navigation')).toBeVisible()
    
    // 测试移动端布局
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.getByRole('button', { name: /菜单/ })).toBeVisible()
  })

  test('API 接口健康检查', async ({ page }) => {
    // 验证 API 可访问性
    const response = await page.request.get('/api/health')
    expect(response.ok()).toBeTruthy()
    
    const data = await response.json()
    expect(data).toHaveProperty('status')
    expect(data.status).toBe('healthy')
  })

  test('WebSocket 连接测试', async ({ page }) => {
    // 验证实时事件连接
    await page.goto('/events')
    await page.waitForLoadState('networkidle')
    
    // 检查事件流容器存在
    await expect(page.getByRole('region', { name: /事件流/ })).toBeVisible()
  })
})

test.describe('自动化升级验证', () => {
  test('版本信息展示', async ({ page }) => {
    await page.goto('/platform')
    
    // 验证版本信息区域存在
    await expect(page.getByText(/版本/)).toBeVisible()
    await expect(page.getByText(/构建/)).toBeVisible()
  })

  test('自动更新检测', async ({ page }) => {
    await page.goto('/platform')
    
    // 验证更新检测按钮存在
    await expect(page.getByRole('button', { name: /检查更新/ })).toBeEnabled()
  })

  test('配置管理页面', async ({ page }) => {
    await page.goto('/platform')
    
    // 验证配置区域存在
    await expect(page.getByRole('region', { name: /配置/ })).toBeVisible()
  })
})