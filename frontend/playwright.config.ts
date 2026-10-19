import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'e2e',
  // The journeys share one seeded database, so they run one after another.
  workers: 1,
  use: {
    baseURL: 'http://localhost:5173',
    // CI and sandboxes may provide a Chromium binary instead of downloading one.
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  webServer: { command: 'pnpm dev', url: 'http://localhost:5173', reuseExistingServer: true, timeout: 60_000 },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
})
