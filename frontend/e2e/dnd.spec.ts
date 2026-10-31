import { expect, test as it, type Locator, type Page } from "@playwright/test"

import { addColumn, login } from "./helpers.ts"

/** Mouse drag in small steps, SortableJS needs real move events. */
async function drag(page: Page, from: Locator, to: Locator) {
  const a = await from.boundingBox()
  const b = await to.boundingBox()
  if (a == null || b == null) throw new Error("element not visible")
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2)
  await page.mouse.down()
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 20 })
  await page.mouse.up()
}

it("drag card to other column persists", async ({ page }) => {
  await login(page)
  await page.getByRole("button", { name: "New Board" }).click()
  await page.getByLabel("Board Name").fill("Dnd")
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page).toHaveURL(/b\/dnd$/u)

  await addColumn(page)
  await addColumn(page)
  const columns = page.locator(".board-column")
  await expect(columns).toHaveCount(2)
  const add = columns.first().getByLabel("Add a card")
  await add.fill("Move me")
  await add.press("Enter")
  await expect(columns.first().locator(".todo-card")).toHaveCount(1)

  await drag(page, columns.first().locator(".card-handle"), columns.nth(1).locator(".card-list"))
  await expect(columns.nth(1).locator(".todo-card")).toHaveCount(1)

  await page.reload()
  await expect(page.locator(".board-column").nth(1).locator("textarea")).toHaveValue("Move me")
})
