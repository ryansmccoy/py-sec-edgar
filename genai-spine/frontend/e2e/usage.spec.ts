import { test, expect } from '@playwright/test'

test.describe('Usage Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /usage/i }).click()
  })

  test('should display usage interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /cost tracking/i })).toBeVisible()
  })

  test('should show usage statistics section', async ({ page }) => {
    await expect(page.getByText(/usage statistics/i)).toBeVisible()
  })

  test('should show model pricing section', async ({ page }) => {
    await expect(page.getByText(/model pricing/i)).toBeVisible()
  })

  test('should show cost estimation info', async ({ page }) => {
    await expect(page.getByText(/cost estimation/i)).toBeVisible()
  })

  test('should display stats cards', async ({ page }) => {
    // Look for stat labels
    await expect(page.getByText(/total requests/i)).toBeVisible()
    await expect(page.getByText(/total tokens/i)).toBeVisible()
    await expect(page.getByText(/total cost/i)).toBeVisible()
  })
})
