import { flushPromises } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { button, mountApp } from "@/__tests__/mount.ts"
import { bulkUpdateCards } from "@/client/index.ts"
import BulkBar from "@/components/BulkBar.vue"
import { useBoardStore } from "@/stores/board.ts"

vi.mock("@/client/index.ts")

describe("BulkBar", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("disabled without selection, applies label to selection", async () => {
    const store = useBoardStore()
    store.labels = [{ id: 3, name: "Work", color: "#ff0000" }]
    const { wrapper } = mountApp(BulkBar)
    expect(button(wrapper, "Work").attributes("disabled")).toBeDefined()

    store.toggleBulk()
    store.toggleSelected(9)
    await flushPromises()
    expect(wrapper.text()).toContain("1 selected")
    await button(wrapper, "Work").trigger("click")
    expect(bulkUpdateCards).toHaveBeenCalledWith({ body: { ids: [9], label_id: 3 } })
    expect(store.bulkMode).toBe(false)
  })
})
