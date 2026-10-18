<script setup lang="ts">
import { useQuasar } from "quasar"
import { computed, watch } from "vue"
import { VueDraggable } from "vue-draggable-plus"
import { useRouter } from "vue-router"

import { deleteBoard } from "@/client/index.ts"
import BoardColumn from "@/components/BoardColumn.vue"
import BulkBar from "@/components/BulkBar.vue"
import BoardEditDialog from "@/components/dialogs/BoardEditDialog.vue"
import DeleteCardsDialog from "@/components/dialogs/DeleteCardsDialog.vue"
import ExportDialog from "@/components/dialogs/ExportDialog.vue"
import ManageLabelsDialog from "@/components/dialogs/ManageLabelsDialog.vue"
import { errorMessage } from "@/services/apiClient.ts"
import { useAuthStore } from "@/stores/auth.ts"
import { useBoardStore } from "@/stores/board.ts"

const props = defineProps<{ boardKey: string }>()
const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()
const store = useBoardStore()

const LAST_BOARD_KEY = "last_board_key"

async function load(key: string) {
  // touch last_login only when switching boards, not on reload
  const touch = sessionStorage.getItem(LAST_BOARD_KEY) !== key
  sessionStorage.setItem(LAST_BOARD_KEY, key)
  store.exitBulk()
  try {
    await Promise.all([store.loadBoard(key, touch), store.loadLabels(), store.loadBoards()])
  } catch (err) {
    $q.notify({ type: "warning", message: errorMessage(err) })
    await router.replace({ name: "boards" })
  }
}

watch(() => props.boardKey, load, { immediate: true })

const columns = computed({
  get: () => store.board?.columns ?? [],
  set: (value) => store.setColumns(value),
})

const boardOptions = computed(() => store.boards.map((b) => ({ label: b.name, value: b.key })))

function switchBoard(key: string) {
  void router.push({ name: "board", params: { key } })
}

function onColumnDrop() {
  if (store.board == null) return
  void store.saveColumnOrder(
    store.board.id,
    columns.value.map((c) => c.id),
  )
}

function openBoardDialog(rename: boolean) {
  const b = store.board
  if (b == null) return
  $q.dialog({
    component: BoardEditDialog,
    componentProps: rename
      ? { title: "Rename Board", boardId: b.id, name: b.name, boardKey: b.key }
      : { title: "New Board" },
  }).onOk(async (key: string) => {
    if (key === b.key) {
      await store.refresh()
    } else {
      await router.push({ name: "board", params: { key } })
    }
  })
}

function confirmDeleteBoard() {
  const b = store.board
  if (b == null) return
  $q.dialog({
    title: "Delete board",
    message: `Delete board '${b.name}' with all columns and cards?`,
    cancel: true,
    ok: { color: "negative", label: "Delete" },
  }).onOk(async () => {
    if (await store.run(() => deleteBoard({ path: { board_id: b.id } }))) {
      await router.replace({ name: "boards" })
    }
  })
}

function openDialog(component: typeof ExportDialog | typeof DeleteCardsDialog) {
  if (store.board == null) return
  $q.dialog({ component, componentProps: { boardId: store.board.id } })
}

function manageLabels() {
  $q.dialog({ component: ManageLabelsDialog }).onDismiss(() => store.refresh())
}

async function logout() {
  authStore.logout()
  await router.replace({ name: "login" })
}
</script>

<template>
  <q-page class="board-page">
    <template v-if="store.board">
      <div class="row items-center no-wrap q-mb-md">
        <q-select
          v-if="store.boards.length > 1"
          :model-value="store.board.key"
          :options="boardOptions"
          emit-value
          map-options
          dense
          borderless
          dark
          options-dense
          class="board-switcher text-h6"
          aria-label="Switch board"
          @update:model-value="switchBoard"
        />
        <h5
          v-else
          class="q-my-none text-white text-weight-bold"
          style="letter-spacing: -0.5px"
        >
          {{ store.board.name }}
        </h5>
        <q-space />
        <div class="row no-wrap text-white">
          <q-btn
            type="button"
            flat
            round
            icon="checklist"
            aria-label="Bulk edit"
            @click="store.toggleBulk()"
          >
            <q-tooltip>Bulk edit</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="swap_vert"
            aria-label="Sort by prio, label, title"
            @click="store.sortCards('prio')"
          >
            <q-tooltip>Sort by prio, label, title</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="calendar_month"
            aria-label="Sort by date"
            @click="store.sortCards('date')"
          >
            <q-tooltip>Sort by date</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="view_column"
            aria-label="Add column"
            @click="store.addColumn(store.board.id)"
          >
            <q-tooltip>Add column</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="download"
            aria-label="Export"
            @click="openDialog(ExportDialog)"
          >
            <q-tooltip>Export</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="sync"
            aria-label="Sync from server"
            @click="store.refresh()"
          >
            <q-tooltip>Sync from server</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            icon="more_vert"
            aria-label="Menu"
          >
            <q-menu auto-close>
              <q-list dense>
                <q-item
                  clickable
                  @click="openBoardDialog(true)"
                >
                  <q-item-section>Rename Board</q-item-section>
                </q-item>
                <q-item
                  clickable
                  @click="openBoardDialog(false)"
                >
                  <q-item-section>New Board</q-item-section>
                </q-item>
                <q-item
                  clickable
                  :to="{ name: 'boards' }"
                >
                  <q-item-section>All Boards</q-item-section>
                </q-item>
                <q-separator />
                <q-item
                  clickable
                  @click="manageLabels"
                >
                  <q-item-section>Manage Labels</q-item-section>
                </q-item>
                <q-separator />
                <q-item
                  clickable
                  @click="openDialog(DeleteCardsDialog)"
                >
                  <q-item-section>Delete Cards</q-item-section>
                </q-item>
                <q-item
                  clickable
                  class="text-negative"
                  @click="confirmDeleteBoard"
                >
                  <q-item-section>Delete Board</q-item-section>
                </q-item>
                <q-separator />
                <q-item
                  clickable
                  @click="logout"
                >
                  <q-item-section>Logout {{ authStore.user?.user_name }}</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </div>

      <BulkBar v-if="store.bulkMode" />

      <VueDraggable
        v-model="columns"
        class="columns-row row no-wrap q-gutter-md"
        handle=".column-handle"
        :animation="150"
        @end="onColumnDrop"
      >
        <BoardColumn
          v-for="column in columns"
          :key="column.id"
          :column="column"
        />
      </VueDraggable>
    </template>
  </q-page>
</template>

<style scoped>
.board-page {
  padding: 16px 24px;
}
.columns-row {
  overflow-x: auto;
  min-height: 400px;
  align-items: flex-start;
}
.board-switcher :deep(.q-field__native) {
  color: white;
  font-weight: bold;
}
@media (max-width: 600px) {
  .board-page {
    padding: 8px;
  }
  .columns-row {
    flex-direction: column;
    flex-wrap: nowrap;
  }
}
</style>
