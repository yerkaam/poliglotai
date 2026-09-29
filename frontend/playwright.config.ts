import { defineConfig, devices } from '@playwright/test';

/** E2E runs against a live stack: `ng serve` (proxying /api to Django) or the Docker Compose build. */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  retries: process.env['CI'] ? 1 : 0,
  use: {
    baseURL: process.env['E2E_BASE_URL'] ?? 'http://localhost:4300',
    trace: 'retain-on-failure',
    locale: 'kk-KZ',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'phone-360', use: { ...devices['Pixel 5'], viewport: { width: 360, height: 780 } } },
  ],
});
