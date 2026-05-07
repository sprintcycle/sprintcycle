import { expect, test } from '@playwright/test'

test('dashboard shell and plan route', async ({ page }) => {
  await page.goto('/plan')
  await expect(page.getByText('SprintCycle', { exact: false }).first()).toBeVisible()
  await expect(page.getByRole('menuitem', { name: /执行计划/ })).toBeVisible()
})

test('history route shell', async ({ page }) => {
  await page.goto('/history')
  await expect(page.getByText('SprintCycle', { exact: false }).first()).toBeVisible()
  await expect(page.getByText('近期执行记录')).toBeVisible()
})
