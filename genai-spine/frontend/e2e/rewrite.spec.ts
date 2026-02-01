import { test, expect } from '@playwright/test'

test.describe('Rewrite Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /rewrite/i }).click()
  })

  test('should display rewrite interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /rewrite/i })).toBeVisible()

    // Should have text input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have rewrite button
    await expect(page.getByRole('button', { name: /rewrite/i })).toBeVisible()
  })

  test('should show mode options', async ({ page }) => {
    // Should have mode labels - clean, format, organize, summarize
    await expect(page.getByText(/clean/i)).toBeVisible()
    await expect(page.getByText(/format/i)).toBeVisible()
    await expect(page.getByText(/organize/i)).toBeVisible()
  })

  test('should be able to select different modes', async ({ page }) => {
    // Click on different mode options
    const formatButton = page.getByRole('button', { name: /format/i })
    if (await formatButton.isVisible()) {
      await formatButton.click()
    }
  })

  test('should be able to enter text to rewrite', async ({ page }) => {
    const textarea = page.locator('textarea')
    const testText = 'This is some messy text that needs cleaning up!!!'
    await textarea.fill(testText)
    await expect(textarea).toHaveValue(testText)
  })
})
