import { test, expect } from '@playwright/test'

test.describe('Health Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display health status', async ({ page }) => {
    // Look for health indicator in sidebar or page
    await page.getByRole('link', { name: /health/i }).click()

    // Should have heading
    await expect(page.getByRole('heading', { name: /service health/i })).toBeVisible()

    // Should show some form of status (may fail if backend not running)
    const statusText = page.getByText(/status|healthy|error|loading/i)
    await expect(statusText.first()).toBeVisible()
  })

  test('should show models section', async ({ page }) => {
    await page.getByRole('link', { name: /health/i }).click()

    // Should have models heading
    await expect(page.getByText(/available models/i)).toBeVisible()
  })
})
