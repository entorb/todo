<script setup lang="ts">
import { useDialogPluginComponent } from "quasar"
import { computed, onMounted, ref } from "vue"

import { useBoardStore } from "@/stores/board.ts"

const props = defineProps<{ mode: "move" | "copy"; sourceColumnName: string }>()
defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK, onDialogCancel } = dialog
const store = useBoardStore()

const boardId = ref<number | null>(store.board?.id ?? null)
const columnId = ref<number | null>(null)

// current board first, then other boards that have columns
const boardOptions = computed(() => {
  const current = store.boards.filter((b) => b.id === store.board?.id)
  const others = store.boards.filter((b) => b.id !== store.board?.id && b.columns.length > 0)
  return [...current, ...others].map((b) => ({ label: b.name, value: b.id }))
})

const columnOptions = computed(
  () =>
    store.boards
      .find((b) => b.id === boardId.value)
      ?.columns.map((c) => ({ label: c.name, value: c.id })) ?? [],
)

/** Default: same column name as source, else first column. */
function selectDefaultColumn() {
  const options = columnOptions.value
  columnId.value =
    options.find((o) => o.label === props.sourceColumnName)?.value ?? options[0]?.value ?? null
}

onMounted(async () => {
  await store.loadBoards()
  selectDefaultColumn()
})
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 300px">
      <q-card-section class="text-h6">
        {{ mode === "move" ? "Move to…" : "Copy to…" }}
      </q-card-section>
      <q-card-section class="column q-gutter-sm">
        <q-select
          v-model="boardId"
          :options="boardOptions"
          label="Board"
          emit-value
          map-options
          @update:model-value="selectDefaultColumn"
        />
        <q-select
          v-model="columnId"
          :options="columnOptions"
          label="Column"
          emit-value
          map-options
        />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn
          type="button"
          flat
          label="Cancel"
          @click="onDialogCancel"
        />
        <q-btn
          type="button"
          color="primary"
          :label="mode === 'move' ? 'Move' : 'Copy'"
          :disable="columnId == null"
          @click="onDialogOK(columnId)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
