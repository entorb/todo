<script setup lang="ts">
import { useQuasar } from "quasar"
import { computed, onUnmounted, watch } from "vue"
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
  localStorage.setItem(LAST_BOARD_KEY, key) // reopened on app start, see router
  store.exitBulk()
  try {
    await Promise.all([store.loadBoard(key, touch), store.loadLabels(), store.loadBoards()])
  } catch (err) {
    localStorage.removeItem(LAST_BOARD_KEY)
    $q.notify({ type: "warning", message: errorMessage(err) })
    await router.replace({ name: "boards" })
  }
}

watch(() => props.boardKey, load, { immediate: true })
watch(
  () => store.board?.name,
  (name) => {
    document.title = name ?? "Todo"
  },
  { immediate: true },
)
onUnmounted(() => {
  document.title = "Todo"
})

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

const darkLabel = computed(() => ($q.dark.isActive ? "Light mode" : "Dark mode"))

function toggleDark() {
  $q.dark.toggle()
  localStorage.setItem("dark", String($q.dark.isActive))
}

// members may only edit cards, board and column options are owner-only
const isOwner = computed(() => store.board?.is_owner ?? false)

const hideLabel = computed(() => (store.hideCompleted ? "Show completed" : "Hide completed"))

// toolbar buttons on desktop, menu items on phones
const allToolbarActions = [
  {
    label: "Sort by prio, label, title",
    icon: "swap_vert",
    ownerOnly: true,
    run: () => store.sortCards("prio"),
  },
  {
    label: "Sort by date",
    icon: "calendar_month",
    ownerOnly: true,
    run: () => store.sortCards("date"),
  },
  {
    label: "Export",
    icon: "download",
    ownerOnly: true,
    run: () => openDialog(ExportDialog),
  },
  { label: "Sync from server", icon: "sync", ownerOnly: false, run: () => store.refresh() },
]
const toolbarActions = computed(() =>
  allToolbarActions.filter((a) => isOwner.value || !a.ownerOnly),
)

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
            :color="store.bulkMode ? 'amber' : undefined"
            :aria-pressed="store.bulkMode"
            aria-label="Bulk edit"
            @click="store.toggleBulk()"
          >
            <q-tooltip>Bulk edit</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            :icon="store.hideCompleted ? 'visibility' : 'visibility_off'"
            :aria-label="hideLabel"
            @click="store.hideCompleted = !store.hideCompleted"
          >
            <q-tooltip>{{ hideLabel }}</q-tooltip>
          </q-btn>
          <q-btn
            type="button"
            flat
            round
            :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
            :aria-label="darkLabel"
            @click="toggleDark"
          >
            <q-tooltip>{{ darkLabel }}</q-tooltip>
          </q-btn>
          <q-btn
            v-for="a in toolbarActions"
            :key="a.label"
            type="button"
            flat
            round
            class="gt-xs"
            :icon="a.icon"
            :aria-label="a.label"
            @click="a.run"
          >
            <q-tooltip>{{ a.label }}</q-tooltip>
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
                  v-for="a in toolbarActions"
                  :key="a.label"
                  clickable
                  class="xs"
                  @click="a.run"
                >
                  <q-item-section>{{ a.label }}</q-item-section>
                </q-item>
                <q-separator class="xs" />
                <q-item
                  v-if="isOwner"
                  clickable
                  @click="store.board != null && store.addColumn(store.board.id)"
                >
                  <q-item-section>Add column</q-item-section>
                </q-item>
                <q-item
                  v-if="isOwner"
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
                <template v-if="isOwner">
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
                </template>
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

      <div
        v-if="columns.length === 0"
        class="column items-center q-pa-xl text-white"
      >
        <div class="text-h6 q-mb-md">
          This board has no columns yet
        </div>
        <q-btn
          v-if="isOwner"
          type="button"
          color="white"
          text-color="primary"
          icon="view_column"
          label="Add first column"
          @click="store.addColumn(store.board.id)"
        />
      </div>
      <VueDraggable
        v-else
        v-model="columns"
        class="columns-row row no-wrap"
        handle=".column-handle"
        :disabled="!isOwner"
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
    <div
      v-else
      class="flex flex-center full-height"
    >
      <q-spinner
        color="white"
        size="3em"
      />
    </div>
  </q-page>
</template>

<style scoped>
/* page fills viewport, columns scroll individually */
.board-page {
  padding: calc(16px + env(safe-area-inset-top)) 24px 16px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.columns-row {
  flex: 1;
  min-height: 0;
  gap: 16px;
  overflow-x: auto;
  align-items: flex-start;
}
.board-switcher :deep(.q-field__native) {
  color: white;
  font-weight: bold;
}
@media (max-width: 600px) {
  .board-page {
    padding: calc(8px + env(safe-area-inset-top)) 8px 8px;
    height: auto;
  }
  .columns-row {
    flex-direction: column;
    flex-wrap: nowrap;
    overflow-x: visible;
  }
}
</style>
