import { test, expect } from '@playwright/test'

test.describe('Extract Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /extract/i }).click()
  })

  test('should display extraction interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /entity extraction/i })).toBeVisible()

    // Should have text input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have extract button
    await expect(page.getByRole('button', { name: /extract/i })).toBeVisible()
  })

  test('should show entity type toggles', async ({ page }) => {
    // Should have entity type labels
    await expect(page.getByText(/PERSON/i)).toBeVisible()
    await expect(page.getByText(/ORG/i)).toBeVisible()
    await expect(page.getByText(/LOCATION/i)).toBeVisible()
  })

  test('should be able to enter text', async ({ page }) => {
    const textarea = page.locator('textarea')
    const testText = 'Apple CEO Tim Cook announced a new product in Cupertino.'
    await textarea.fill(testText)
    await expect(textarea).toHaveValue(testText)
  })
})
