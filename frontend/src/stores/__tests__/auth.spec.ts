import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { login } from "@/client/index.ts"
import { tokenManager } from "@/services/apiClient.ts"
import { useAuthStore } from "@/stores/auth.ts"
import { decodeJwt, isTokenExpired } from "@/utils/jwt.ts"

vi.mock("@/utils/jwt", () => ({ decodeJwt: vi.fn(), isTokenExpired: vi.fn() }))
vi.mock("@/client/index.ts", () => ({ login: vi.fn() }))
vi.mock("@/services/apiClient", () => ({
  errorMessage: (err: unknown) => (err instanceof Error ? err.message : "Request failed"),
  tokenManager: { get: vi.fn(), set: vi.fn(), clear: vi.fn() },
}))

const PAYLOAD = { user_id: 1, username: "Torben", exp: Date.now() / 1000 + 3600 }

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("starts logged out", () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.error).toBeNull()
  })

  it("login stores token and user", async () => {
    vi.mocked(login).mockResolvedValue({ data: { access_token: "tok" } } as never)
    vi.mocked(decodeJwt).mockReturnValue(PAYLOAD)
    const store = useAuthStore()
    await store.login("secret")
    expect(tokenManager.set).toHaveBeenCalledWith("tok")
    expect(store.user).toEqual({ user_name: "Torben" })
    expect(store.isLoading).toBe(false)
  })

  it("login failure sets error and rethrows", async () => {
    vi.mocked(login).mockRejectedValue(new Error("Invalid credentials"))
    const store = useAuthStore()
    await expect(store.login("wrong")).rejects.toThrow("Invalid credentials")
    expect(store.error).toBe("Invalid credentials")
    expect(store.isAuthenticated).toBe(false)
  })

  it("undecodable token is rejected and not stored", async () => {
    vi.mocked(login).mockResolvedValue({ data: { access_token: "bad" } } as never)
    vi.mocked(decodeJwt).mockReturnValue(null)
    const store = useAuthStore()
    await expect(store.login("secret")).rejects.toThrow("decode")
    expect(tokenManager.set).not.toHaveBeenCalled()
  })

  it("loadUserFromToken restores valid, clears expired token", () => {
    const store = useAuthStore()
    vi.mocked(tokenManager.get).mockReturnValue("tok")
    vi.mocked(isTokenExpired).mockReturnValue(false)
    vi.mocked(decodeJwt).mockReturnValue(PAYLOAD)
    store.loadUserFromToken()
    expect(store.isAuthenticated).toBe(true)

    vi.mocked(isTokenExpired).mockReturnValue(true)
    store.loadUserFromToken()
    expect(store.isAuthenticated).toBe(false)
    expect(tokenManager.clear).toHaveBeenCalled()
  })
})
