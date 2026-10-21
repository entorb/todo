import { flushPromises } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { button, dialogOk, menuItem, mountApp } from "@/__tests__/mount.ts"
import { createColumn, deleteBoard, getBoard, listBoards, listLabels } from "@/client/index.ts"
import { useAuthStore } from "@/stores/auth.ts"
import BoardListView from "@/views/BoardListView.vue"
import BoardView from "@/views/BoardView.vue"
import LoginView from "@/views/LoginView.vue"

vi.mock("@/client/index.ts")

const BOARDS = [
  { id: 1, key: "a", name: "Alpha", columns: [] },
  { id: 2, key: "b", name: "Beta", columns: [] },
]

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  sessionStorage.clear()
  document.body.innerHTML = ""
  vi.mocked(listBoards).mockResolvedValue({ data: BOARDS } as never)
  vi.mocked(listLabels).mockResolvedValue({ data: [] } as never)
})

describe("LoginView", () => {
  it("logs in and navigates to boards", async () => {
    const { wrapper, router } = mountApp(LoginView)
    const login = vi.spyOn(useAuthStore(), "login").mockResolvedValue()
    await wrapper.find('input[type="password"]').setValue("s3cret")
    await wrapper.find("form").trigger("submit")
    await flushPromises()
    expect(login).toHaveBeenCalledWith("s3cret")
    expect(router.currentRoute.value.name).toBe("boards")
  })

  it("shows error and stays on failed login", async () => {
    const { wrapper, router } = mountApp(LoginView)
    const auth = useAuthStore()
    vi.spyOn(auth, "login").mockImplementation(() => {
      auth.error = "Invalid secret"
      return Promise.reject(new Error("Invalid secret"))
    })
    const replace = vi.spyOn(router, "replace")
    await wrapper.find('input[type="password"]').setValue("wrong")
    await wrapper.find("form").trigger("submit")
    await flushPromises()
    expect(wrapper.text()).toContain("Invalid secret")
    expect(replace).not.toHaveBeenCalled()
  })
})

describe("BoardListView", () => {
  it("lists boards, opens new board after create", async () => {
    const { wrapper, router } = mountApp(BoardListView)
    await flushPromises()
    expect(wrapper.text()).toContain("Alpha")
    expect(wrapper.text()).toContain("Beta")

    dialogOk(wrapper.vm.$q, "new")
    await button(wrapper, "New Board").trigger("click")
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe("/b/new")
  })

  it("shows empty state", async () => {
    vi.mocked(listBoards).mockResolvedValue({ data: [] } as never)
    const { wrapper } = mountApp(BoardListView)
    await flushPromises()
    expect(wrapper.text()).toContain("No boards yet")
  })
})

describe("BoardView", () => {
  const board = (isOwner: boolean, columns: unknown[] = [{ id: 7, name: "Todo", cards: [] }]) => ({
    id: 1,
    key: "a",
    name: "Alpha",
    is_owner: isOwner,
    columns,
  })

  it("loads board, touches last_login only when switching boards", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: board(true) } as never)
    const { wrapper } = mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    expect(getBoard).toHaveBeenCalledWith({ path: { key: "a" }, query: { touch: true } })
    expect(wrapper.find("[data-column-id]").exists()).toBe(true)
    expect(document.title).toBe("Alpha")

    mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    expect(getBoard).toHaveBeenLastCalledWith({ path: { key: "a" }, query: { touch: false } })
  })

  it("hides owner-only actions for members", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: board(true) } as never)
    const { wrapper: owner } = mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    expect(owner.find('[aria-label="Export"]').exists()).toBe(true)

    vi.mocked(getBoard).mockResolvedValue({ data: board(false) } as never)
    const { wrapper: member } = mountApp(BoardView, { boardKey: "b" })
    await flushPromises()
    expect(member.find('[aria-label="Export"]').exists()).toBe(false)
    expect(member.find('[aria-label="Sync from server"]').exists()).toBe(true)
  })

  it("empty board offers first column", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: board(true, []) } as never)
    const { wrapper } = mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    await button(wrapper, "Add first column").trigger("click")
    expect(createColumn).toHaveBeenCalledWith({ body: { board_id: 1 } })
  })

  it("unknown board redirects to board list", async () => {
    vi.mocked(getBoard).mockRejectedValue(new Error("Not found"))
    const { router } = mountApp(BoardView, { boardKey: "x" })
    const replace = vi.spyOn(router, "replace")
    await flushPromises()
    expect(replace).toHaveBeenCalledWith({ name: "boards" })
  })
  it("delete board after confirm returns to board list", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: board(true) } as never)
    const { wrapper, router } = mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    dialogOk(wrapper.vm.$q)
    const replace = vi.spyOn(router, "replace")
    await menuItem(wrapper.find('[aria-label="Menu"]'), "Delete Board")
    expect(deleteBoard).toHaveBeenCalledWith({ path: { board_id: 1 } })
    expect(replace).toHaveBeenCalledWith({ name: "boards" })
  })

  it("rename to same key refreshes, new key navigates", async () => {
    vi.mocked(getBoard).mockResolvedValue({ data: board(true) } as never)
    const { wrapper, router } = mountApp(BoardView, { boardKey: "a" })
    await flushPromises()
    const menu = wrapper.find('[aria-label="Menu"]')

    dialogOk(wrapper.vm.$q, "a")
    vi.mocked(getBoard).mockClear()
    await menuItem(menu, "Rename Board")
    expect(getBoard).toHaveBeenCalledTimes(1)

    dialogOk(wrapper.vm.$q, "z")
    await menuItem(menu, "Rename Board")
    expect(router.currentRoute.value.fullPath).toBe("/b/z")
  })
})
