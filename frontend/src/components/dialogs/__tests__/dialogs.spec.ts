import { flushPromises, type VueWrapper } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { button, dialogOk, mountApp, seedBoard } from "@/__tests__/mount.ts"
import {
  createBoard,
  createLabel,
  deletableCards,
  deleteCards,
  deleteLabel,
  exportBoard,
  listBoards,
  listLabels,
  updateBoard,
  updateLabel,
} from "@/client/index.ts"
import BoardEditDialog from "@/components/dialogs/BoardEditDialog.vue"
import DeleteCardsDialog from "@/components/dialogs/DeleteCardsDialog.vue"
import ExportDialog from "@/components/dialogs/ExportDialog.vue"
import LabelEditorDialog from "@/components/dialogs/LabelEditorDialog.vue"
import LabelPickerDialog from "@/components/dialogs/LabelPickerDialog.vue"
import ManageLabelsDialog from "@/components/dialogs/ManageLabelsDialog.vue"
import MoveCopyDialog from "@/components/dialogs/MoveCopyDialog.vue"
import { useBoardStore } from "@/stores/board.ts"
import { copyHtml, copyText } from "@/utils/clipboard.ts"

vi.mock("@/client/index.ts")
vi.mock("@/utils/clipboard.ts")

const LABELS = [
  { id: 3, name: "Work", color: "#ff0000" },
  { id: 4, name: "Home", color: "#00ff00" },
]

async function submit(wrapper: VueWrapper) {
  await wrapper.find("form").trigger("submit")
  await flushPromises()
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe("BoardEditDialog", () => {
  it("requires name, creates board with lowercased name as default key", async () => {
    vi.mocked(createBoard).mockResolvedValue({ data: { key: "my board" } } as never)
    const { wrapper } = mountApp(BoardEditDialog, { title: "New Board" })
    await submit(wrapper)
    expect(wrapper.text()).toContain("Board name is required")
    expect(createBoard).not.toHaveBeenCalled()

    await wrapper.findAll("input")[0]?.setValue(" My Board ")
    await submit(wrapper)
    expect(createBoard).toHaveBeenCalledWith({ body: { name: "My Board", key: "my board" } })
    expect(wrapper.emitted("ok")).toEqual([["my board"]])
  })

  it("renames existing board, shows server error", async () => {
    vi.mocked(updateBoard).mockRejectedValue(new Error("Key exists"))
    const { wrapper } = mountApp(BoardEditDialog, {
      title: "Rename",
      boardId: 1,
      name: "A",
      boardKey: "a",
    })
    await submit(wrapper)
    expect(updateBoard).toHaveBeenCalledWith({
      path: { board_id: 1 },
      body: { name: "A", key: "a" },
    })
    expect(wrapper.text()).toContain("Key exists")
    expect(wrapper.emitted("ok")).toBeUndefined()
  })
})

describe("LabelEditorDialog", () => {
  it("validates hex color, saves normalized color", async () => {
    const { wrapper } = mountApp(LabelEditorDialog)
    const [name, color] = wrapper.findAll("input")
    await name?.setValue("Urgent")
    await color?.setValue("red")
    await submit(wrapper)
    expect(wrapper.text()).toContain("Color must be hex")

    await color?.setValue(" #FF8800 ")
    await submit(wrapper)
    expect(createLabel).toHaveBeenCalledWith({ body: { name: "Urgent", color: "#ff8800" } })
    expect(wrapper.emitted("ok")).toHaveLength(1)
  })

  it("updates existing label", async () => {
    const { wrapper } = mountApp(LabelEditorDialog, { label: LABELS[0] })
    await submit(wrapper)
    expect(updateLabel).toHaveBeenCalledWith({
      path: { label_id: 3 },
      body: { name: "Work", color: "#ff0000" },
    })
  })
})

describe("LabelPickerDialog", () => {
  it("returns label id or null", async () => {
    useBoardStore().labels = LABELS
    const { wrapper } = mountApp(LabelPickerDialog)
    await button(wrapper, "Home").trigger("click")
    await button(wrapper, "Remove label").trigger("click")
    expect(wrapper.emitted("ok")).toEqual([[4], [null]])
  })
})

describe("ManageLabelsDialog", () => {
  it("delete and edit reload labels", async () => {
    seedBoard({ id: 1, key: "b", columns: [] })
    useBoardStore().labels = LABELS
    vi.mocked(listLabels).mockResolvedValue({ data: [] } as never)
    const { wrapper } = mountApp(ManageLabelsDialog)
    dialogOk(wrapper.vm.$q)

    await wrapper.findAll('[aria-label="Delete label"]')[1]?.trigger("click")
    await flushPromises()
    expect(deleteLabel).toHaveBeenCalledWith({ path: { label_id: 4 } })
    expect(listLabels).toHaveBeenCalledTimes(1)

    await button(wrapper, "Create New Label").trigger("click")
    await flushPromises()
    expect(listLabels).toHaveBeenCalledTimes(2)
  })
})

describe("MoveCopyDialog", () => {
  const BOARDS = [
    {
      id: 2,
      name: "Other",
      columns: [
        { id: 20, name: "Backlog" },
        { id: 21, name: "Done" },
      ],
    },
    { id: 3, name: "Empty", columns: [] },
    { id: 1, name: "Current", columns: [{ id: 10, name: "Todo" }] },
  ]

  it("lists current board first, skips empty boards, preselects same column name", async () => {
    useBoardStore().board = { id: 1 } as never
    vi.mocked(listBoards).mockResolvedValue({ data: BOARDS } as never)
    const { wrapper } = mountApp(MoveCopyDialog, { mode: "move", sourceColumnName: "Done" })
    await flushPromises()
    const [board, column] = wrapper.findAllComponents({ name: "QSelect" })
    expect(board?.props("options")).toEqual([
      { label: "Current", value: 1 },
      { label: "Other", value: 2 },
    ])
    // current board has no "Done" column -> first column
    expect(column?.props("modelValue")).toBe(10)

    board?.vm.$emit("update:modelValue", 2)
    await flushPromises()
    expect(column?.props("modelValue")).toBe(21)
    await button(wrapper, "Move").trigger("click")
    expect(wrapper.emitted("ok")).toEqual([[21]])
  })
})

describe("ExportDialog", () => {
  it("copies html as html, other formats as text", async () => {
    vi.mocked(exportBoard).mockResolvedValue({ data: { text: "x" } } as never)
    const { wrapper } = mountApp(ExportDialog, { boardId: 1 })
    await button(wrapper, "Copy").trigger("click")
    await flushPromises()
    expect(exportBoard).toHaveBeenCalledWith({
      path: { board_id: 1 },
      query: { fmt: "txt", completed_only: true },
    })
    expect(copyText).toHaveBeenCalledWith("x")
    expect(wrapper.emitted("ok")).toHaveLength(1)

    await button(wrapper, "HTML").trigger("click")
    await button(wrapper, "Copy").trigger("click")
    await flushPromises()
    expect(copyHtml).toHaveBeenCalledWith("x")
  })

  it("stays open on error", async () => {
    vi.mocked(exportBoard).mockRejectedValue(new Error("boom"))
    const { wrapper } = mountApp(ExportDialog, { boardId: 1 })
    await button(wrapper, "Copy").trigger("click")
    await flushPromises()
    expect(copyText).not.toHaveBeenCalled()
    expect(wrapper.emitted("ok")).toBeUndefined()
  })
})

describe("DeleteCardsDialog", () => {
  it("previews cards grouped by column, reloads on mode change, deletes", async () => {
    seedBoard({
      id: 1,
      key: "b",
      columns: [
        { id: 7, name: "Todo" },
        { id: 8, name: "Done" },
      ],
    })
    vi.mocked(deletableCards).mockResolvedValue({
      data: [
        { id: 1, column_id: 8, title: "a" },
        { id: 2, column_id: 7, title: "b" },
        { id: 3, column_id: 8, title: "c" },
      ],
    } as never)
    const { wrapper } = mountApp(DeleteCardsDialog, { boardId: 1 })
    await flushPromises()
    expect(wrapper.findAll(".text-weight-bold").map((e) => e.text())).toEqual(["Done", "Todo"])

    await button(wrapper, "All").trigger("click")
    await flushPromises()
    expect(deletableCards).toHaveBeenLastCalledWith({
      path: { board_id: 1 },
      query: { mode: "all" },
    })

    await button(wrapper, "Delete").trigger("click")
    await flushPromises()
    expect(deleteCards).toHaveBeenCalledWith({ path: { board_id: 1 }, query: { mode: "all" } })
    expect(wrapper.emitted("ok")).toHaveLength(1)
  })

  it("nothing to delete disables delete", async () => {
    vi.mocked(deletableCards).mockResolvedValue({ data: [] } as never)
    const { wrapper } = mountApp(DeleteCardsDialog, { boardId: 1 })
    await flushPromises()
    expect(wrapper.text()).toContain("No cards to delete")
    expect(button(wrapper, "Delete").attributes("disabled")).toBeDefined()
  })
})
