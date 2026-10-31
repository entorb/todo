import { expect, test as it } from "@playwright/test"

import { addColumn, login } from "./helpers.ts"

it("create board, column, cards; complete; export", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"])
  await login(page)

  await page.getByRole("button", { name: "New Board" }).click()
  await page.getByLabel("Board Name").fill("Planning")
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page).toHaveURL(/todo\/b\/planning$/u)

  await addColumn(page)
  const addCard = page.getByLabel("Add a card")
  for (const title of ["Buy milk", "Write report"]) {
    await addCard.fill(title)
    await addCard.press("Enter")
    await expect(page.locator(".todo-card textarea").last()).toHaveValue(title)
  }

  const milk = page.locator(".todo-card").first()
  await milk.getByRole("checkbox", { name: "Completed" }).click()
  await expect(milk.getByRole("checkbox", { name: "Completed" })).toHaveAttribute(
    "aria-checked",
    "true",
  )

  await page.getByRole("button", { name: "Export" }).click()
  await page.getByRole("button", { name: "Markdown" }).click()
  await page.getByRole("button", { name: "Copy" }).click()
  await expect(page.getByText("Copied to clipboard")).toBeVisible()
  const text = await page.evaluate(() => navigator.clipboard.readText())
  expect(text).toBe("## Planning\n\n### New Column\n- Buy milk\n")

  // reload keeps data
  await page.reload()
  await expect(page.locator(".todo-card textarea")).toHaveCount(2)
})
