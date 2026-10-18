import { createPinia } from "pinia"
import { Quasar } from "quasar"
import { createApp } from "vue"

import App from "./App.vue"
import quasarConfig from "./plugins/quasar.ts"
import router from "./router/index.ts"
import { installUnauthorizedHandler } from "./services/apiClient.ts"
import { useAuthStore } from "./stores/auth.ts"

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Quasar, quasarConfig)

// expired/invalid token -> back to login
installUnauthorizedHandler(async () => {
  useAuthStore().logout()
  if (router.currentRoute.value.name !== "login") {
    await router.replace({ name: "login" })
  }
})

app.mount("#app")
