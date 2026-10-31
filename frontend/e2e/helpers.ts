import type { Page } from "@playwright/test"

export async function login(page: Page) {
  await page.goto("login")
  await page.locator('input[type="password"]').fill("test")
  await page.getByRole("button", { name: "Login" }).click()
  await page.waitForURL(/todo\/$/u)
}

/** "Add column" lives in the board's 3-dot menu. */
export async function addColumn(page: Page) {
  await page.getByRole("button", { name: "Menu" }).click()
  await page.getByText("Add column", { exact: true }).click()
}
