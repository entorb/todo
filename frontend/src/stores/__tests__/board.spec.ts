import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { bulkUpdateCards, getBoard, updateCard } from "@/client/index.ts"
import { useBoardStore } from "@/stores/board.ts"

vi.mock("quasar", () => ({ Notify: { create: vi.fn() } }))
vi.mock("@/client/index.ts", () => ({
  bulkUpdateCards: vi.fn(),
  getBoard: vi.fn(),
  updateCard: vi.fn(),
}))
vi.mock("@/services/apiClient", () => ({
  errorMessage: (err: unknown) => (err instanceof Error ? err.message : "Request failed"),
}))

const BOARD = { id: 1, key: "b", name: "B", last_login: null, columns: [] }

describe("board store", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(getBoard).mockResolvedValue({ data: BOARD } as never)
  })

  it("mutation reloads board, error returns false", async () => {
    const store = useBoardStore()
    await store.loadBoard("b")
    vi.mocked(getBoard).mockClear()

    expect(await store.patchCard(5, { prio: true })).toBe(true)
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { prio: true } })
    expect(getBoard).toHaveBeenCalledTimes(1)

    vi.mocked(updateCard).mockRejectedValue(new Error("Not found"))
    expect(await store.patchCard(5, { prio: true })).toBe(false)
  })

  it("bulk update sends selection and exits bulk mode", async () => {
    const store = useBoardStore()
    store.toggleBulk()
    store.toggleSelected(1)
    store.toggleSelected(2)
    store.toggleSelected(2)
    await store.bulkUpdate({ label_id: null })
    expect(bulkUpdateCards).toHaveBeenCalledWith({ body: { ids: [1], label_id: null } })
    expect(store.bulkMode).toBe(false)
    expect(store.selected.size).toBe(0)
  })

  it("bulk update without selection does nothing", async () => {
    const store = useBoardStore()
    store.toggleBulk()
    await store.bulkUpdate({ prio: true })
    expect(bulkUpdateCards).not.toHaveBeenCalled()
  })
})
