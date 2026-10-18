/**
 * API client configuration using generated OpenAPI client
 */

import { isAxiosError } from "axios"

import { client } from "@/client/client.gen.ts"
import { config } from "@/config/env.ts"
import { isTokenExpired } from "@/utils/jwt.ts"

client.setConfig({
  baseURL: config.apiBaseUrl,
})

// Token management helpers
export const tokenManager = {
  get(): string | null {
    return localStorage.getItem("access_token")
  },

  set(token: string): void {
    localStorage.setItem("access_token", token)
  },

  clear(): void {
    localStorage.removeItem("access_token")
  },
}

// Setup token injection for authenticated requests
// Checks token expiry before each request
client.setConfig({
  auth() {
    const token = tokenManager.get()
    return token != null && !isTokenExpired(token) ? token : ""
  },
})

/** Call handler on 401 responses (expired / invalid token). */
export function installUnauthorizedHandler(handler: () => Promise<void>): void {
  client.instance.interceptors.response.use(undefined, async (error: unknown) => {
    if (isAxiosError(error) && error.response?.status === 401) {
      await handler()
    }
    throw error
  })
}

/** User facing message from API error (FastAPI `detail`) or Error. */
export function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail: unknown = error.response?.data?.detail
    if (typeof detail === "string") return detail
    return error.message
  }
  return error instanceof Error ? error.message : "Request failed"
}
