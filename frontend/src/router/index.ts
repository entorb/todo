/**
 * Vue Router configuration
 *
 * Includes a chunk-load error handler: after a new deployment the browser
 * may still hold a cached index.html that references old hashed chunk
 * filenames.  When the dynamic import fails we force a full page reload
 * so the browser fetches the latest assets.
 */

import { createRouter, createWebHistory, type RouteLocationRaw } from "vue-router"

import { tokenManager } from "@/services/apiClient.ts"
import { useAuthStore } from "@/stores/auth.ts"

/**
 * Wrap a lazy component import so that a chunk-load failure (e.g. after a
 * new deploy) triggers a single hard reload instead of a blank page.
 */
function lazyLoad(loader: () => Promise<unknown>) {
  return async () => {
    try {
      return await loader()
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : ""
      if (
        msg.includes("dynamically imported module") ||
        msg.includes("preload CSS") ||
        msg.includes("Loading chunk") ||
        msg.includes("net::ERR_ABORTED")
      ) {
        // Prevent infinite reload loops
        const key = "chunk-reload"
        if (sessionStorage.getItem(key) == null) {
          sessionStorage.setItem(key, "1")
          globalThis.location.reload()
          return new Promise(() => {
            /* intentionally pending forever */
          })
        }
        sessionStorage.removeItem(key)
      }
      throw error
    }
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "boards",
      component: lazyLoad(async () => import("@/views/BoardListView.vue")),
    },
    {
      path: "/b/:key",
      name: "board",
      component: lazyLoad(async () => import("@/views/BoardView.vue")),
      props: (route) => ({ boardKey: String(route.params["key"]) }),
    },
    {
      path: "/login",
      name: "login",
      component: lazyLoad(async () => import("@/views/LoginView.vue")),
      meta: { requiresAuth: false },
    },
    { path: "/:pathMatch(.*)*", redirect: { name: "boards" } },
  ],
})

// eslint-disable-next-line sonarjs/function-return-type -- guard returns redirect or true
router.beforeEach((to): RouteLocationRaw | true => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta["requiresAuth"] !== false

  if (!authStore.isAuthenticated && tokenManager.get() != null) {
    authStore.loadUserFromToken()
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    return { name: "login" }
  }
  if (to.name === "login" && authStore.isAuthenticated) {
    return { name: "boards" }
  }
  return true
})

export default router
