import { test, expect } from '@playwright/test'

test.describe('Title Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /title/i }).click()
  })

  test('should display title inference interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /title inference/i })).toBeVisible()

    // Should have text input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have generate button
    await expect(page.getByRole('button', { name: /generate/i })).toBeVisible()
  })

  test('should have max words slider', async ({ page }) => {
    await expect(page.getByText(/max words/i)).toBeVisible()

    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()
  })

  test('should be able to enter content for title', async ({ page }) => {
    const textarea = page.locator('textarea')
    const testContent = 'This article discusses the latest trends in artificial intelligence and machine learning...'
    await textarea.fill(testContent)
    await expect(textarea).toHaveValue(testContent)
  })
})
