import { flushPromises } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { VueDraggable } from "vue-draggable-plus"
import { mountApp, seedBoard } from "@/__tests__/mount.ts"
import { createCard, moveCard, updateColumn } from "@/client/index.ts"
import BoardColumn from "@/components/BoardColumn.vue"

vi.mock("@/client/index.ts")

const COLUMN = {
  id: 7,
  name: "Todo",
  cards: [
    { id: 1, column_id: 7, title: "open", date_completed: null },
    { id: 2, column_id: 7, title: "done", date_completed: "2026-01-01" },
  ],
}

function setup(isOwner = true) {
  seedBoard({ id: 1, key: "b", is_owner: isOwner, columns: [COLUMN] })
  return mountApp(BoardColumn, { column: COLUMN })
}

describe("BoardColumn", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("renders cards and open/total count", () => {
    const { wrapper } = setup()
    expect(wrapper.findAll("[data-card-id]")).toHaveLength(2)
    expect(wrapper.text()).toContain("1/2")
  })

  it("owner can rename, non-owner cannot", async () => {
    const { wrapper } = setup()
    await wrapper.find('[aria-label="Column name"]').setValue(" Doing ")
    wrapper.findComponent({ name: "QInput" }).vm.$emit("blur")
    expect(updateColumn).toHaveBeenCalledWith({ path: { column_id: 7 }, body: { name: "Doing" } })

    const { wrapper: guest } = setup(false)
    expect(guest.find('[aria-label="Column name"]').attributes("readonly")).toBeDefined()
    expect(guest.find('[aria-label="Delete column"]').exists()).toBe(false)
  })

  it("adds trimmed card on enter, ignores blank", async () => {
    const { wrapper } = setup()
    const input = wrapper.find('[aria-label="Add a card"]')
    await input.setValue("   ")
    await input.trigger("keydown", { key: "Enter" })
    expect(createCard).not.toHaveBeenCalled()

    await input.setValue(" Milk ")
    await input.trigger("keydown", { key: "Enter" })
    await flushPromises()
    expect(createCard).toHaveBeenCalledWith({ body: { column_id: 7, title: "Milk" } })
    expect((input.element as HTMLInputElement).value).toBe("")
  })

  it("drop persists position only when moved", () => {
    const { wrapper } = setup()
    const list = { dataset: { columnId: "7" } }
    const drop = (to: object, oldIndex: number, newIndex: number) =>
      wrapper.findComponent(VueDraggable).vm.$emit("end", {
        item: { dataset: { cardId: "1" } },
        from: list,
        to,
        oldIndex,
        newIndex,
      })

    drop(list, 0, 0)
    expect(moveCard).not.toHaveBeenCalled()
    drop(list, 0, 1)
    expect(moveCard).toHaveBeenLastCalledWith({
      path: { card_id: 1 },
      body: { column_id: 7, position: 1 },
    })
    drop({ dataset: { columnId: "8" } }, 0, 0)
    expect(moveCard).toHaveBeenLastCalledWith({
      path: { card_id: 1 },
      body: { column_id: 8, position: 0 },
    })
  })
})
