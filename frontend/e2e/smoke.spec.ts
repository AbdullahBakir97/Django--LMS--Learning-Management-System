import { expect, test } from '@playwright/test'

// Runs against the dev server with no backend: the refresh call fails and the app lands on sign-in.
test('unauthenticated visit lands on sign-in in both themes', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await page.getByRole('button', { name: /switch to dark theme/i }).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await page.getByRole('link', { name: 'Create an account' }).click()
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
})
