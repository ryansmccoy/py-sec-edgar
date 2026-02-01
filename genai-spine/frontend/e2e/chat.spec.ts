import { test, expect } from '@playwright/test'

test.describe('Chat Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /chat/i }).click()
  })

  test('should display chat interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /chat completion/i })).toBeVisible()

    // Should have message input
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have send button
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible()
  })

  test('should have model selector', async ({ page }) => {
    // Should have model dropdown or selector
    const modelSelect = page.locator('select').first()
    await expect(modelSelect).toBeVisible()
  })

  test('should have temperature slider', async ({ page }) => {
    // Look for temperature label and slider
    await expect(page.getByText(/temperature/i)).toBeVisible()

    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()
  })

  test('should be able to type message', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.fill('Hello, AI!')
    await expect(textarea).toHaveValue('Hello, AI!')
  })
})
