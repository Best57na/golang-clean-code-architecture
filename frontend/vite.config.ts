import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// In development the API runs separately, so proxy /api to it (no CORS needed).
// In Docker, nginx does the same proxying (see nginx.conf).
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:3000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': apiTarget,
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
})
