import { test, expect } from '@playwright/test'

test.describe('Prompts Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /prompts/i }).click()
  })

  test('should display prompts interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /prompt/i })).toBeVisible()
  })

  test('should show prompts list or empty state', async ({ page }) => {
    // Either shows prompts or "no prompts" message
    const contentArea = page.locator('main')
    await expect(contentArea).toBeVisible()

    // Should have some content - either prompts or empty message
    const hasPrompts = await page.getByText(/template|prompt/i).count() > 0
    const hasEmptyState = await page.getByText(/no prompts/i).count() > 0

    expect(hasPrompts || hasEmptyState).toBeTruthy()
  })
})
