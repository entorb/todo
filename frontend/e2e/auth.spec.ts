import { expect, test } from "@playwright/test"

import { login } from "./helpers.ts"

test("redirects to login when not authenticated", async ({ page }) => {
  await page.goto("")
  await expect(page).toHaveURL(/todo-vue\/login$/)
  await expect(page.getByRole("button", { name: "Login" })).toBeVisible()
})

test("logs in with a valid secret", async ({ page }) => {
  await login(page)
  await expect(page.getByText("Select Board")).toBeVisible()
})

test("shows an error for a wrong secret", async ({ page }) => {
  await page.goto("login")
  await page.locator('input[type="password"]').fill("wrong-secret")
  await page.getByRole("button", { name: "Login" }).click()
  await expect(page.locator(".bg-negative")).toContainText("Invalid credentials")
  await expect(page).toHaveURL(/todo-vue\/login$/)
})

test("logs out", async ({ page }) => {
  await login(page)
  await page.getByRole("button", { name: "Logout" }).click()
  await expect(page).toHaveURL(/todo-vue\/login$/)
})
