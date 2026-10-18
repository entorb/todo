<script setup lang="ts">
import { useQuasar } from "quasar"
import { onMounted } from "vue"
import { useRouter } from "vue-router"

import BoardEditDialog from "@/components/dialogs/BoardEditDialog.vue"
import { useAuthStore } from "@/stores/auth.ts"
import { useBoardStore } from "@/stores/board.ts"

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()
const store = useBoardStore()

onMounted(() => store.loadBoards())

function newBoard() {
  $q.dialog({ component: BoardEditDialog, componentProps: { title: "New Board" } }).onOk(
    (key: string) => router.push({ name: "board", params: { key } }),
  )
}

async function logout() {
  authStore.logout()
  await router.replace({ name: "login" })
}
</script>

<template>
  <q-page class="flex flex-center">
    <q-card style="min-width: 300px">
      <q-card-section class="row items-center">
        <div class="text-h6 col">
          Select Board
        </div>
        <q-btn
          type="button"
          flat
          round
          icon="logout"
          aria-label="Logout"
          @click="logout"
        >
          <q-tooltip>Logout {{ authStore.user?.user_name }}</q-tooltip>
        </q-btn>
      </q-card-section>
      <q-list separator>
        <q-item
          v-for="b in store.boards"
          :key="b.id"
          clickable
          :to="{ name: 'board', params: { key: b.key } }"
        >
          <q-item-section>{{ b.name }}</q-item-section>
        </q-item>
        <q-item v-if="store.boards.length === 0">
          <q-item-section class="text-grey">
            No boards yet
          </q-item-section>
        </q-item>
      </q-list>
      <q-card-actions align="right">
        <q-btn
          type="button"
          flat
          color="primary"
          icon="add"
          label="New Board"
          @click="newBoard"
        />
      </q-card-actions>
    </q-card>
  </q-page>
</template>
