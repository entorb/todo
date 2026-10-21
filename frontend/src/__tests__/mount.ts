import { type DOMWrapper, flushPromises, mount } from "@vue/test-utils"
import { createPinia, getActivePinia, setActivePinia } from "pinia"
import { Dialog, Notify, Quasar, type QVueGlobals } from "quasar"
import { vi } from "vitest"
import { type Component, type DefineComponent, defineComponent, h } from "vue"
import { createMemoryHistory, createRouter } from "vue-router"

import { getBoard } from "@/client/index.ts"
import { useBoardStore } from "@/stores/board.ts"

/** QDialog (teleported, hidden) and QPage (needs QLayout): render slot inline. */
const SlotStub = defineComponent({
  emits: ["hide"],
  setup(_, { slots, expose }) {
    expose({
      show() {
        /* no-op */
      },
      hide() {
        /* no-op */
      },
    })
    return () => h("div", slots["default"]?.())
  },
})

const Empty = { render: () => null }

function testRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "boards", component: Empty },
      { path: "/b/:key", name: "board", component: Empty },
      { path: "/login", name: "login", component: Empty },
    ],
  })
}

/** Mount with Quasar, active (else fresh) pinia and memory router. */
export function mountApp(component: Component, props: Record<string, unknown> = {}) {
  let pinia = getActivePinia()
  if (pinia == null) {
    pinia = createPinia()
    setActivePinia(pinia)
  }
  const router = testRouter()
  const wrapper = mount(component as DefineComponent, {
    props,
    global: {
      plugins: [[Quasar, { plugins: { Notify, Dialog } }], pinia, router],
      stubs: { QDialog: SlotStub, QPage: SlotStub },
    },
  })
  return { wrapper, router }
}

/** Replace $q.dialog: every dialog resolves OK with `payload`. */
export function dialogOk($q: QVueGlobals, payload?: unknown) {
  return vi.spyOn($q, "dialog").mockImplementation(() => {
    const chain = {
      onOk: (cb: (p: unknown) => unknown) => {
        void cb(payload)
        return chain
      },
      onDismiss: (cb: () => unknown) => {
        void cb()
        return chain
      },
    }
    return chain as never
  })
}

/** Find button by its label text. */
export function button(
  wrapper: { findAll: (s: string) => Array<DOMWrapper<Element>> },
  label: string,
) {
  const btn = wrapper.findAll("button").find((b) => b.text().endsWith(label))
  if (btn == null) throw new Error(`button ${label} not found`)
  return btn
}

/** Set current board, board reload (store.refresh) returns it again. Needs mocked client. */
export function seedBoard(board: object) {
  // biome-ignore lint/correctness/useHookAtTopLevel: pinia store, not a React hook
  useBoardStore().board = board as never
  vi.mocked(getBoard).mockResolvedValue({ data: board } as never)
}

/** Open QMenu via its button, click menu item (QMenu teleports to body). */
export async function menuItem(trigger: DOMWrapper<Element>, label: string) {
  await trigger.trigger("click")
  await flushPromises()
  const item = [...document.body.querySelectorAll(".q-menu .q-item")].find(
    (e) => e.textContent?.trim() === label,
  )
  if (!(item instanceof HTMLElement)) throw new Error(`menu item ${label} not found`)
  item.click()
  await flushPromises()
}
