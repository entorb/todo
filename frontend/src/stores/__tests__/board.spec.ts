import { createPinia, setActivePinia } from "pinia"
import { Notify } from "quasar"
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

  it("patch applies response locally, error reloads board and returns false", async () => {
    const card = { id: 5, column_id: 7, title: "t", prio: null }
    vi.mocked(getBoard).mockResolvedValue({
      data: { ...BOARD, columns: [{ id: 7, name: "c", cards: [card] }] },
    } as never)
    const store = useBoardStore()
    await store.loadBoard("b")
    vi.mocked(getBoard).mockClear()

    vi.mocked(updateCard).mockResolvedValue({ data: { ...card, prio: true } } as never)
    expect(await store.patchCard(5, { prio: true })).toBe(true)
    expect(updateCard).toHaveBeenCalledWith({ path: { card_id: 5 }, body: { prio: true } })
    expect(store.board?.columns[0]?.cards[0]?.prio).toBe(true)
    expect(getBoard).not.toHaveBeenCalled()

    vi.mocked(updateCard).mockRejectedValue(new Error("Not found"))
    expect(await store.patchCard(5, { prio: true })).toBe(false)
    expect(getBoard).toHaveBeenCalledTimes(1)
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

describe("board store run / optimistic updates", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("run notifies on error and always reloads board", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: BOARD } as never)
    const store = useBoardStore()
    await store.loadBoard("b")
    vi.mocked(getBoard).mockClear()

    expect(await store.run(async () => Promise.reject(new Error("Conflict")))).toBe(false)
    expect(Notify.create).toHaveBeenCalledWith({ type: "warning", message: "Conflict" })
    expect(await store.run(async () => Promise.resolve())).toBe(true)
    expect(getBoard).toHaveBeenCalledTimes(2)
  })

  it("sortCards without board is a no-op", async () => {
    const store = useBoardStore()
    expect(await store.sortCards("prio")).toBe(false)
    expect(getBoard).not.toHaveBeenCalled()
  })
})
