import { defineConfig } from '@playwright/test'

// Runs against the Docker Compose stack: `docker compose up --build`, then `npm run test:e2e`.
// Set PW_CHANNEL=msedge or chrome to use an installed browser instead of `npx playwright install`.
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8080',
    channel: process.env.PW_CHANNEL,
    trace: 'retain-on-failure',
  },
})
