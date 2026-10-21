import { flushPromises } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { dialogOk, menuItem, mountApp, seedBoard } from "@/__tests__/mount.ts"
import { type CardPublic, copyCard, moveCard, updateCard } from "@/client/index.ts"
import TodoCard from "@/components/TodoCard.vue"
import { useBoardStore } from "@/stores/board.ts"

vi.mock("@/client/index.ts")

const CARD = {
  id: 5,
  column_id: 7,
  title: "Buy milk https://shop.example",
  prio: null,
  is_revive: false,
  label_id: null,
  date_completed: null,
} as unknown as CardPublic

function setup(card: Partial<CardPublic> = {}) {
  return mountApp(TodoCard, { card: { ...CARD, ...card }, columnName: "Todo" })
}

describe("TodoCard", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    document.body.innerHTML = ""
    vi.mocked(updateCard).mockResolvedValue({ data: CARD } as never)
  })

  it("renders title and link button", () => {
    const { wrapper } = setup()
    expect(wrapper.find("textarea").element.value).toBe(CARD.title)
    expect(wrapper.find('[aria-label="Open link"]').attributes("href")).toBe("https://shop.example")
  })

  it("saves trimmed changed title, reverts empty title", async () => {
    const { wrapper } = setup()
    const input = wrapper.find("textarea")
    // QInput emits blur deferred after focusout, emit directly
    const blur = async () => wrapper.findComponent({ name: "QInput" }).vm.$emit("blur")
    await input.setValue("  New  ")
    await blur()
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { title: "New" } })

    vi.mocked(updateCard).mockClear()
    await input.setValue("   ")
    await blur()
    expect(updateCard).not.toHaveBeenCalled()
    expect(input.element.value).toBe(CARD.title)
  })

  it("checkbox toggles completed", async () => {
    const { wrapper } = setup()
    await wrapper.find('[aria-label="Completed"]').trigger("click")
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { is_completed: true } })
  })

  it("bulk mode: click selects card, hides card actions", async () => {
    const { wrapper } = setup()
    const store = useBoardStore()
    store.toggleBulk()
    await flushPromises()
    expect(wrapper.find('[aria-label="Card menu"]').exists()).toBe(false)
    await wrapper.find('[aria-label="Select card"]').trigger("click")
    expect(store.selected.has(5)).toBe(true)
    expect(wrapper.classes()).toContain("selected")
  })
  it("label picker sets label", async () => {
    useBoardStore().labels = [{ id: 3, name: "Work", color: "#ff0000" }]
    const { wrapper } = setup()
    dialogOk(wrapper.vm.$q, 3)
    await wrapper.find('[aria-label="Set label"]').trigger("click")
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { label_id: 3 } })
  })

  it("menu: move and copy to chosen column", async () => {
    seedBoard({ id: 1, key: "b", columns: [] })
    const { wrapper } = setup()
    const dialog = dialogOk(wrapper.vm.$q, 8)
    const notify = vi.spyOn(wrapper.vm.$q, "notify")
    const menu = wrapper.find('[aria-label="Card menu"]')

    await menuItem(menu, "Move to…")
    expect(dialog.mock.calls[0]?.[0].componentProps).toEqual({
      mode: "move",
      sourceColumnName: "Todo",
    })
    expect(moveCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { column_id: 8 } })
    expect(notify).toHaveBeenLastCalledWith({ message: "Card moved" })

    vi.mocked(copyCard).mockRejectedValue(new Error("nope"))
    notify.mockClear()
    await menuItem(menu, "Copy to…")
    expect(copyCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { column_id: 8 } })
    expect(notify).not.toHaveBeenCalledWith({ message: "Card copied" })
  })

  it("menu offers only other prio states", async () => {
    const { wrapper } = setup({ prio: true })
    await menuItem(wrapper.find('[aria-label="Card menu"]'), "Remove Prio")
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { prio: null } })
    const labels = [...document.body.querySelectorAll(".q-menu .q-item")].map((e) =>
      e.textContent?.trim(),
    )
    expect(labels).not.toContain("Mark Important")
  })
})
