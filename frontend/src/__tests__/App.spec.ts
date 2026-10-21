import { flushPromises } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { h } from "vue"
import { mountApp } from "@/__tests__/mount.ts"
import App from "@/App.vue"

// QLayout observes its size, jsdom has no ResizeObserver
vi.stubGlobal(
  "ResizeObserver",
  class {
    observe() {
      /* no-op */
    }
    unobserve() {
      /* no-op */
    }
    disconnect() {
      /* no-op */
    }
  },
)

describe("App", () => {
  it("renders routed view inside layout", async () => {
    const { wrapper, router } = mountApp(App)
    router.addRoute({ path: "/x", component: { render: () => h("p", "routed") } })
    await router.push("/x")
    await flushPromises()
    expect(wrapper.find(".q-layout p").text()).toBe("routed")
  })
})
