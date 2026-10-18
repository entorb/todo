<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { useAuthStore } from "@/stores/auth.ts"

const router = useRouter()
const authStore = useAuthStore()
const username = ref("") // dummy field, added for password manager compatibility
const secret = ref("")
const secretInput = ref<{ focus: () => void } | null>(null)
onMounted(() => secretInput.value?.focus())

async function handleLogin() {
  try {
    await authStore.login(secret.value)
  } catch {
    // Login itself failed — error is already set in store
    return
  }

  // If the lazy-loaded chunk fails (e.g. stale deploy), fall back to a hard
  // navigation so the browser fetches fresh assets.
  try {
    const failure = await router.replace({ name: "boards" })
    if (failure) {
      globalThis.location.replace(router.resolve({ name: "boards" }).href)
    }
  } catch {
    globalThis.location.replace(router.resolve({ name: "boards" }).href)
  }
}
</script>

<template>
  <q-page class="flex flex-center">
    <div style="width: 100%; max-width: 400px; padding: 20px">
      <q-card>
        <q-card-section>
          <div class="text-h5 text-center">
            Todo
          </div>
        </q-card-section>

        <q-card-section>
          <q-form @submit.prevent="handleLogin">
            <!-- Hidden username field for password managers -->
            <label
              for="username"
              style="display: none"
            >Name</label>
            <input
              id="username"
              v-model="username"
              type="text"
              autocomplete="username"
              style="display: none"
              tabindex="-1"
              aria-hidden="true"
            />

            <q-input
              ref="secretInput"
              v-model="secret"
              label="Secret"
              type="password"
              :disable="authStore.isLoading"
              autocomplete="current-password"
              outlined
              required
              class="q-mb-md"
            />

            <q-banner
              v-if="authStore.error"
              class="bg-negative text-white q-mb-md"
              rounded
            >
              {{ authStore.error }}
            </q-banner>

            <q-btn
              type="submit"
              color="primary"
              :loading="authStore.isLoading"
              :disable="!secret"
              unelevated
              size="lg"
              class="full-width"
              label="Login"
            />
          </q-form>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>
