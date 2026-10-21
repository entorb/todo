import { AxiosError, type AxiosResponse } from "axios"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { client } from "@/client/client.gen.ts"
import { errorMessage, installUnauthorizedHandler, tokenManager } from "@/services/apiClient.ts"
import { isTokenExpired } from "@/utils/jwt.ts"

vi.mock("@/utils/jwt", () => ({ isTokenExpired: vi.fn() }))
vi.mock("@/client/client.gen.ts", () => ({
  client: { setConfig: vi.fn(), instance: { interceptors: { response: { use: vi.fn() } } } },
}))

function axiosError(status: number, data: unknown): AxiosError {
  return new AxiosError("Request failed with status code", "ERR", undefined, undefined, {
    status,
    data,
  } as AxiosResponse)
}

describe("errorMessage", () => {
  it("prefers FastAPI detail string, falls back to message", () => {
    expect(errorMessage(axiosError(409, { detail: "Name exists" }))).toBe("Name exists")
    // validation errors (422) have a list as detail
    expect(errorMessage(axiosError(422, { detail: [{ msg: "x" }] }))).toBe(
      "Request failed with status code",
    )
    expect(errorMessage(new Error("boom"))).toBe("boom")
    expect(errorMessage("weird")).toBe("Request failed")
  })
})

describe("auth token injection", () => {
  // first setConfig call: baseURL, second: auth
  const auth = vi.mocked(client.setConfig).mock.calls[1]?.[0].auth as () => string

  beforeEach(() => vi.mocked(localStorage.getItem).mockReset())

  it("sends valid token only", () => {
    expect(auth()).toBe("")
    vi.mocked(localStorage.getItem).mockReturnValue("tok")
    vi.mocked(isTokenExpired).mockReturnValue(false)
    expect(auth()).toBe("tok")
    vi.mocked(isTokenExpired).mockReturnValue(true)
    expect(auth()).toBe("")
    expect(tokenManager.get()).toBe("tok")
  })
})

describe("installUnauthorizedHandler", () => {
  it("calls handler on 401 only and rethrows", async () => {
    const handler = vi.fn().mockResolvedValue(undefined)
    installUnauthorizedHandler(handler)
    const onError = vi.mocked(client.instance.interceptors.response.use).mock.calls[0]?.[1]
    if (onError == null) throw new Error("no interceptor")

    const err403 = axiosError(403, {})
    await expect(onError(err403)).rejects.toBe(err403)
    expect(handler).not.toHaveBeenCalled()

    const err401 = axiosError(401, {})
    await expect(onError(err401)).rejects.toBe(err401)
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
