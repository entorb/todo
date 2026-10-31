import { expect, test as it, test } from "@playwright/test"

import { login } from "./helpers.ts"

it("redirects to login when not authenticated", async ({ page }) => {
  await page.goto("")
  await expect(page).toHaveURL(/todo\/login(\?redirect=.*)?$/u)
  await expect(page.getByRole("button", { name: "Login" })).toBeVisible()
})

it("logs in with a valid secret", async ({ page }) => {
  await login(page)
  await expect(page.getByText("Select Board")).toBeVisible()
})

it("shows an error for a wrong secret", async ({ page }) => {
  await page.goto("login")
  await page.locator('input[type="password"]').fill("wrong-secret")
  await page.getByRole("button", { name: "Login" }).click()
  await expect(page.locator(".bg-negative")).toContainText("Invalid credentials")
  await expect(page).toHaveURL(/todo\/login(\?redirect=.*)?$/u)
})

it("logs out", async ({ page }) => {
  await login(page)
  await page.getByRole("button", { name: "Logout" }).click()
  await expect(page).toHaveURL(/todo\/login(\?redirect=.*)?$/u)
})
