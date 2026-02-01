import { test, expect } from '@playwright/test'

test.describe('Commit Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /commit/i }).click()
  })

  test('should display commit message interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /commit message/i })).toBeVisible()

    // Should have diff input area
    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()

    // Should have generate button
    await expect(page.getByRole('button', { name: /generate/i })).toBeVisible()
  })

  test('should have sample diff button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /sample/i })).toBeVisible()
  })

  test('should fill sample diff on button click', async ({ page }) => {
    const textarea = page.locator('textarea')

    // Clear textarea first
    await textarea.fill('')

    // Click sample diff button
    await page.getByRole('button', { name: /sample/i }).click()

    // Textarea should now have content
    await expect(textarea).not.toHaveValue('')
  })

  test('should be able to enter diff manually', async ({ page }) => {
    const textarea = page.locator('textarea')
    const testDiff = `diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
`
    await textarea.fill(testDiff)
    await expect(textarea).toContainText('diff --git')
  })
})
