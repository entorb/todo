import { defineStore } from "pinia"
import { computed, ref } from "vue"

import { login as apiLogin } from "@/client/index.ts"
import { errorMessage, tokenManager } from "@/services/apiClient.ts"
import { decodeJwt, isTokenExpired } from "@/utils/jwt.ts"

interface UserInfo {
  user_name: string
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserInfo | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => user.value !== null)

  async function login(secret: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await apiLogin({ body: { secret } })
      const payload = decodeJwt(data.access_token)
      if (payload == null) {
        throw new Error("Failed to decode authentication token")
      }
      tokenManager.set(data.access_token)
      user.value = { user_name: payload.username }
    } catch (err) {
      error.value = errorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function loadUserFromToken(): void {
    const token = tokenManager.get()
    if (token == null || isTokenExpired(token)) {
      logout()
      return
    }
    const payload = decodeJwt(token)
    user.value = payload ? { user_name: payload.username } : null
  }

  function logout(): void {
    tokenManager.clear()
    user.value = null
    error.value = null
  }

  return { user, isLoading, error, isAuthenticated, login, logout, loadUserFromToken }
})
