import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should load home page and show sidebar', async ({ page }) => {
    await page.goto('/')

    // Check sidebar navigation items exist
    await expect(page.getByRole('link', { name: /health/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /chat/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /summarize/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /extract/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /classify/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /rewrite/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /title/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /commit/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /prompts/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /usage/i })).toBeVisible()
  })

  test('should navigate to all pages', async ({ page }) => {
    await page.goto('/')

    // Click through each nav item
    const navItems = [
      { link: /health/i, heading: /service health/i },
      { link: /chat/i, heading: /chat completion/i },
      { link: /summarize/i, heading: /summarization/i },
      { link: /extract/i, heading: /entity extraction/i },
      { link: /classify/i, heading: /classification/i },
      { link: /rewrite/i, heading: /rewrite/i },
      { link: /title/i, heading: /title inference/i },
      { link: /commit/i, heading: /commit message/i },
      { link: /prompts/i, heading: /prompt/i },
      { link: /usage/i, heading: /cost tracking/i },
    ]

    for (const { link, heading } of navItems) {
      await page.getByRole('link', { name: link }).click()
      await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    }
  })
})
