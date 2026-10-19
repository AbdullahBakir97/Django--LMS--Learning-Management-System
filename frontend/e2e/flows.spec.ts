import { expect, test, type Page } from '@playwright/test'

// The main journeys against a real, seeded backend (`seed_demo`). Run with E2E_BACKEND=1 and
// DEMO_PASSWORD set to the seed's password; CI's e2e job does both.
test.skip(!process.env.E2E_BACKEND, 'needs a seeded backend')

const PASSWORD = process.env.DEMO_PASSWORD ?? ''
// A 1×1 PNG, so the image upload path runs without a fixture file.
const PIXEL = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)

async function signIn(page: Page, name: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(`${name}@demo.lms`)
  await page.getByLabel('Password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).not.toHaveURL(/\/login/)
}

test('a learner finds a course through search', async ({ page }) => {
  await signIn(page, 'lina')
  await expect(page.getByRole('heading', { name: 'Hello, Lina' })).toBeVisible()
  await page.keyboard.press('Control+k')
  await page.getByRole('combobox', { name: 'Search everything' }).fill('django rest')
  await page.getByRole('option', { name: /APIs with Django REST Framework/ }).click()
  await expect(page.getByRole('heading', { name: 'APIs with Django REST Framework' })).toBeVisible()
})

test('a learner posts with a photo', async ({ page }) => {
  await signIn(page, 'lina')
  const note = `Study notes ${Date.now()}`
  await page.getByLabel('Write a post').fill(note)
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'notes.png',
    mimeType: 'image/png',
    buffer: PIXEL,
  })
  await page.getByRole('button', { name: 'Post', exact: true }).click()
  const post = page.getByRole('article', { name: 'Post by Lina Haddad' }).filter({ hasText: note })
  await expect(post.getByRole('img', { name: 'Image 1 of 1' })).toBeVisible()
})

test('a moderator removes a reported post', async ({ page }) => {
  await signIn(page, 'sara')
  await page.getByRole('link', { name: 'Moderation' }).click()
  await expect(page.getByText('Cheap followers and course certificates')).toBeVisible()
  await page.getByRole('button', { name: 'Remove post' }).click()
  await page.getByRole('button', { name: 'Remove post' }).click() // confirm
  await expect(page.getByText('Nothing to review.')).toBeVisible()
})

test('an instructor opens course analytics', async ({ page }) => {
  await signIn(page, 'karim')
  await page.getByRole('link', { name: 'Teaching' }).click()
  await page.getByRole('link', { name: 'Analytics' }).first().click()
  await expect(page.getByRole('heading', { name: 'Where learners stop' })).toBeVisible()
  await expect(page.getByText('Enrolled', { exact: true })).toBeVisible()
})

test('an admin reads the platform overview', async ({ page }) => {
  await signIn(page, 'sara')
  await page.getByRole('link', { name: 'Overview' }).click()
  await expect(page.getByRole('heading', { name: 'Courses in demand' })).toBeVisible()
  await expect(page.getByRole('main').getByText('People', { exact: true })).toBeVisible()
})

test('a paid course asks for payment instead of enrolling', async ({ page }) => {
  await signIn(page, 'omar')
  await page.goto('/courses')
  await page.getByRole('link', { name: /Testing Django properly/ }).click()
  await expect(page.getByText('$29.00')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Buy course' })).toBeVisible()
})
