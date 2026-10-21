import process from "node:process"
import { defineConfig, devices } from "@playwright/test"

// e2e uses its own DB with a test user, see e2e/global-setup.ts
const E2E_ENV = "DB_PATH=sqlite-e2e.db JWT_SECRET_KEY=e2e-secret-e2e-secret-e2e-secret-e2e"

export default defineConfig({
  testDir: "./e2e",
  timeout: 10_000,
  fullyParallel: false,
  workers: 2,
  quiet: true,
  retries: 0,
  reporter: "list",
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: "http://localhost:5173/todo/",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `cd ../backend && ${E2E_ENV} uv run --no-build uvicorn app.main:app --host localhost --port 9003`,
      url: "http://localhost:9003/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "pnpm dev",
      url: "http://localhost:5173/todo/",
      reuseExistingServer: !process.env["CI"],
      timeout: 120_000,
    },
  ],
})
