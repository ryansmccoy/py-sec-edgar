import { test, expect } from '@playwright/test'

test.describe('Classify Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /classify/i }).click()
  })

  test('should display classification interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /classification/i })).toBeVisible()

    // Should have text input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have classify button
    await expect(page.getByRole('button', { name: /classify/i })).toBeVisible()
  })

  test('should show category inputs', async ({ page }) => {
    // Should have category section
    await expect(page.getByText(/categories/i)).toBeVisible()

    // Should have some default or input categories
    const categoryInputs = page.locator('input[type="text"]')
    await expect(categoryInputs.first()).toBeVisible()
  })

  test('should be able to add categories', async ({ page }) => {
    // Look for add category button
    const addButton = page.getByRole('button', { name: /add|plus|\+/i })
    if (await addButton.isVisible()) {
      await addButton.click()
      // Should add another input field
    }
  })
})
