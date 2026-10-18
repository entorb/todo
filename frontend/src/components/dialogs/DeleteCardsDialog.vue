<script setup lang="ts">
import { Notify, useDialogPluginComponent } from "quasar"
import { computed, ref, watch } from "vue"

import { type CardPublic, deletableCards, deleteCards, updateCard } from "@/client/index.ts"
import { errorMessage } from "@/services/apiClient.ts"
import { useBoardStore } from "@/stores/board.ts"

type Mode = "completed" | "all" | "2w"

const props = defineProps<{ boardId: number }>()
defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK, onDialogCancel } = dialog
const store = useBoardStore()

const mode = ref<Mode>("completed")
const preview = ref<CardPublic[]>([])

const columnName = computed(
  () => new Map(store.board?.columns.map((c) => [c.id, c.name]) ?? []),
)
const grouped = computed(() => {
  const groups = new Map<string, CardPublic[]>()
  for (const card of preview.value) {
    const name = columnName.value.get(card.column_id) ?? ""
    groups.set(name, [...(groups.get(name) ?? []), card])
  }
  return [...groups.entries()]
})

async function loadPreview() {
  try {
    preview.value = (
      await deletableCards({ path: { board_id: props.boardId }, query: { mode: mode.value } })
    ).data
  } catch (err) {
    Notify.create({ type: "warning", message: errorMessage(err) })
  }
}

watch(mode, loadPreview, { immediate: true })

/** Mark as repeat -> excluded from delete. */
async function markRepeat(card: CardPublic) {
  await store.run(() => updateCard({ path: { card_id: card.id }, body: { is_repeat: true } }))
  await loadPreview()
}

async function doDelete() {
  const ok = await store.run(() =>
    deleteCards({ path: { board_id: props.boardId }, query: { mode: mode.value } }),
  )
  if (ok) onDialogOK()
}
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 320px; max-width: 90vw">
      <q-card-section class="text-h6">
        Delete Cards
      </q-card-section>
      <q-card-section class="column q-gutter-sm">
        <q-btn-toggle
          v-model="mode"
          spread
          no-caps
          :options="[
            { label: 'Completed', value: 'completed' },
            { label: 'All', value: 'all' },
            { label: 'Completed > 2 weeks', value: '2w' },
          ]"
        />
        <div class="text-caption text-grey-7">
          Repeat cards will not be deleted.
        </div>
      </q-card-section>
      <q-card-section
        class="scroll"
        style="max-height: 50vh"
      >
        <div v-if="preview.length === 0">
          No cards to delete.
        </div>
        <div
          v-for="[name, cards] in grouped"
          :key="name"
          class="q-mb-sm"
        >
          <div class="text-weight-bold">
            {{ name }}
          </div>
          <div
            v-for="card in cards"
            :key="card.id"
            class="row items-center no-wrap"
          >
            <q-btn
              type="button"
              flat
              round
              dense
              size="sm"
              icon="repeat"
              aria-label="Mark as repeat (keep)"
              @click="markRepeat(card)"
            >
              <q-tooltip>Mark as repeat (keep)</q-tooltip>
            </q-btn>
            <span class="ellipsis">{{ card.title }}</span>
          </div>
        </div>
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
          color="negative"
          label="Delete"
          :disable="preview.length === 0"
          @click="doDelete"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
