import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import router from "@/router/index.ts"
import { tokenManager } from "@/services/apiClient.ts"
import { useAuthStore } from "@/stores/auth.ts"

const stub = { default: { render: () => null } }
vi.mock("@/views/BoardListView.vue", () => stub)
vi.mock("@/views/BoardView.vue", () => stub)
vi.mock("@/views/LoginView.vue", () => stub)
vi.mock("@/services/apiClient", () => ({ tokenManager: { get: vi.fn(), clear: vi.fn() } }))

describe("router guard", () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    vi.mocked(tokenManager.get).mockReturnValue(null)
    await router.push("/login")
  })

  it("redirects anonymous users to login", async () => {
    await router.push("/b/abc")
    expect(router.currentRoute.value.name).toBe("login")
  })

  it("restores session from stored token", async () => {
    const auth = useAuthStore()
    const load = vi.spyOn(auth, "loadUserFromToken").mockImplementation(() => {
      auth.user = { user_name: "u" }
    })
    vi.mocked(tokenManager.get).mockReturnValue("tok")
    await router.push("/b/abc")
    expect(load).toHaveBeenCalled()
    expect(router.currentRoute.value.params["key"]).toBe("abc")
  })

  it("keeps logged-in users away from login", async () => {
    const auth = useAuthStore()
    auth.user = { user_name: "u" }
    await router.push("/b/abc")
    await router.push("/login")
    expect(router.currentRoute.value.name).toBe("boards")
  })
})
