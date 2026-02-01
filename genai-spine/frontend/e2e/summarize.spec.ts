import { test, expect } from '@playwright/test'

test.describe('Summarize Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /summarize/i }).click()
  })

  test('should display summarization interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /summarization/i })).toBeVisible()

    // Should have text input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have summarize button
    await expect(page.getByRole('button', { name: /summarize/i })).toBeVisible()
  })

  test('should have sample text button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /sample/i })).toBeVisible()
  })

  test('should fill sample text on button click', async ({ page }) => {
    const textarea = page.locator('textarea')

    // Clear textarea first
    await textarea.fill('')

    // Click sample text button
    await page.getByRole('button', { name: /sample/i }).click()

    // Textarea should now have content
    await expect(textarea).not.toHaveValue('')
  })

  test('should have max sentences slider', async ({ page }) => {
    await expect(page.getByText(/max sentences/i)).toBeVisible()

    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()
  })
})
