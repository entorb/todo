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
const newTitle = ref("")
// drag & drop updates the list optimistically, server order follows via moveCardTo
const cards = computed({
  get: () => props.column.cards,
  set: (value: CardPublic[]) => store.setCards(props.column.id, value),
})
const addInput = ref<{ focus: () => void } | null>(null)

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
        name="drag_indicator"
        class="column-handle cursor-move"
      />
      <q-input
        v-model="name"
        class="col text-weight-bold"
        borderless
        dense
        aria-label="Column name"
        @blur="saveName"
        @keydown.enter.prevent="($event.target as HTMLElement).blur()"
      />
      <q-btn
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
    />
  </div>
</template>

<style scoped>
.board-column {
  width: 300px;
  min-width: 280px;
  max-width: 320px;
  background: #eceff1;
  border-radius: 10px;
  padding: 12px;
  gap: 3px;
  align-self: flex-start;
}
.card-list {
  gap: 3px;
  min-height: 20px;
}
.add-card {
  background: rgb(255 255 255 / 50%);
  border-radius: 6px;
  padding: 0 8px;
}
:deep(.card-ghost) {
  opacity: 0.4;
  background: #cfd8dc !important;
}
@media (max-width: 600px) {
  .board-column {
    width: 100%;
    max-width: 100%;
  }
}
</style>
