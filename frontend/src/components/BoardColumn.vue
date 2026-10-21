<script setup lang="ts">
import { useQuasar } from "quasar"
import { computed, nextTick, ref, watch } from "vue"
import { type DraggableEvent, VueDraggable } from "vue-draggable-plus"

import type { CardPublic, ColumnPublic } from "@/client/index.ts"
import TodoCard from "@/components/TodoCard.vue"
import { useBoardStore } from "@/stores/board.ts"

const props = defineProps<{ column: ColumnPublic }>()
const $q = useQuasar()
const store = useBoardStore()

const name = ref("")
watch(
  () => props.column.name,
  (n) => {
    name.value = n
  },
  { immediate: true },
)
const isOwner = computed(() => store.board?.is_owner ?? false)
const newTitle = ref("")
// drag & drop updates the list optimistically, server order follows via moveCardTo
const cards = computed({
  get: () => props.column.cards,
  set: (value: CardPublic[]) => store.setCards(props.column.id, value),
})
const openCount = computed(() => cards.value.filter((c) => c.date_completed == null).length)
const addInput = ref<{ focus: () => void } | null>(null)

function revertName(event: KeyboardEvent) {
  name.value = props.column.name
  ;(event.target as HTMLElement).blur()
}

function saveName() {
  const n = name.value.trim()
  if (n === "" || n === props.column.name) {
    name.value = props.column.name
    return
  }
  void store.renameColumn(props.column.id, n)
}

async function addCard() {
  const t = newTitle.value.trim()
  if (t === "") return
  newTitle.value = ""
  await store.addCard(props.column.id, t)
  await nextTick()
  addInput.value?.focus()
}

function confirmDelete() {
  $q.dialog({
    title: "Delete column",
    message: "Delete this column and all its cards?",
    cancel: true,
    ok: { color: "negative", label: "Delete" },
  }).onOk(() => store.removeColumn(props.column.id))
}

/** Card dropped (same or other column): persist new position. */
function onCardDrop(event: DraggableEvent) {
  const cardId = Number(event.item.dataset["cardId"])
  const targetColumnId = Number(event.to.dataset["columnId"])
  if (event.newIndex == null) return
  if (event.from === event.to && event.oldIndex === event.newIndex) return
  void store.moveCardTo(cardId, targetColumnId, event.newIndex)
}
</script>

<template>
  <div
    class="board-column column no-wrap"
    :data-column-id="column.id"
  >
    <div class="row items-center no-wrap">
      <q-icon
        v-if="isOwner"
        name="drag_indicator"
        class="column-handle cursor-move"
      />
      <q-input
        v-model="name"
        class="col"
        input-class="text-weight-bold text-subtitle1"
        borderless
        dense
        :readonly="!isOwner"
        aria-label="Column name"
        @blur="saveName"
        @keydown.enter.prevent="($event.target as HTMLElement).blur()"
        @keydown.esc="revertName"
      />
      <q-badge
        rounded
        color="blue-grey-3"
        text-color="blue-grey-10"
        class="q-mr-xs"
        :label="`${openCount}/${cards.length}`"
      >
        <q-tooltip>open / total</q-tooltip>
      </q-badge>
      <q-btn
        v-if="isOwner"
        type="button"
        flat
        round
        dense
        size="sm"
        icon="delete_outline"
        style="opacity: 0.5"
        aria-label="Delete column"
        @click="confirmDelete"
      />
    </div>
    <VueDraggable
      v-model="cards"
      class="column no-wrap card-list"
      :data-column-id="column.id"
      group="cards"
      handle=".card-handle"
      :animation="150"
      ghost-class="card-ghost"
      @end="onCardDrop"
    >
      <TodoCard
        v-for="card in cards"
        v-show="!(store.hideCompleted && card.date_completed != null)"
        :key="card.id"
        :card="card"
        :column-name="column.name"
      />
    </VueDraggable>
    <q-input
      ref="addInput"
      v-model="newTitle"
      class="add-card"
      dense
      borderless
      placeholder="+ Add a card…"
      aria-label="Add a card"
      @keydown.enter.prevent="addCard"
    >
      <template
        v-if="newTitle.trim() !== ''"
        #append
      >
        <q-btn
          type="button"
          flat
          round
          dense
          size="sm"
          icon="send"
          aria-label="Add card"
          @click="addCard"
        />
      </template>
    </q-input>
  </div>
</template>

<style scoped>
.board-column {
  width: 300px;
  min-width: 280px;
  max-width: 320px;
  max-height: 100%;
  background: var(--column-bg);
  border-radius: 10px;
  padding: 12px;
  gap: 3px;
  align-self: flex-start;
}
.card-list {
  gap: 3px;
  min-height: 20px;
  overflow-y: auto;
  flex: 0 1 auto;
  padding: 3px; /* room for shadow / selection outline */
}
.add-card {
  flex-shrink: 0;
  background: var(--add-card-bg);
  border-radius: 6px;
  padding: 0 8px;
}
/* overlay instead of background: TodoCard sets background inline */
:deep(.card-ghost) {
  opacity: 0.4;
}
:deep(.card-ghost)::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 2;
  background: var(--ghost-bg);
  border-radius: inherit;
}
@media (max-width: 600px) {
  .board-column {
    width: 100%;
    max-width: 100%;
    max-height: none;
  }
}
</style>
