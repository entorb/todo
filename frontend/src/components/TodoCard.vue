<script setup lang="ts">
import { useQuasar } from "quasar"
import { computed, ref, watch } from "vue"

import type { CardPublic } from "@/client/index.ts"
import LabelPickerDialog from "@/components/dialogs/LabelPickerDialog.vue"
import MoveCopyDialog from "@/components/dialogs/MoveCopyDialog.vue"
import { useBoardStore } from "@/stores/board.ts"
import { contrastColor, findUrl } from "@/utils/color.ts"

const props = defineProps<{ card: CardPublic; columnName: string }>()
const $q = useQuasar()
const store = useBoardStore()

const title = ref("")
watch(
  () => props.card.title,
  (t) => {
    title.value = t
  },
  { immediate: true },
)

const label = computed(() =>
  props.card.label_id == null ? undefined : store.labelById.get(props.card.label_id),
)
const isCompleted = computed(() => props.card.date_completed != null)
const url = computed(() => findUrl(props.card.title))
const isSelected = computed(() => store.selected.has(props.card.id))

const cardStyle = computed(() => {
  if (label.value != null) {
    return {
      background: label.value.color,
      color: contrastColor(label.value.color),
      opacity: isCompleted.value ? 0.45 : 1,
    }
  }
  return {
    background: isCompleted.value ? "var(--card-done-bg)" : "var(--card-bg)",
    color: "var(--card-fg)",
    opacity: isCompleted.value ? 0.5 : 1,
  }
})

const titleStyle = computed(() => ({
  fontWeight: props.card.prio === true ? "bold" : "normal",
  fontStyle: props.card.prio === false ? "italic" : "normal",
}))

function saveTitle() {
  const t = title.value.trim()
  if (t === "" || t === props.card.title) {
    title.value = props.card.title
    return
  }
  void store.patchCard(props.card.id, { title: t })
}

function revertTitle(event: KeyboardEvent) {
  title.value = props.card.title
  ;(event.target as HTMLElement).blur()
}

function toggleCompleted(value: boolean) {
  void store.patchCard(props.card.id, { is_completed: value })
}

function setPrio(prio: boolean | null) {
  void store.patchCard(props.card.id, { prio })
}

function setRevive(isRepeat: boolean) {
  void store.patchCard(props.card.id, { is_revive: isRepeat })
}

function pickLabel() {
  $q.dialog({ component: LabelPickerDialog }).onOk((labelId: number | null) =>
    store.patchCard(props.card.id, { label_id: labelId }),
  )
}

function moveOrCopy(mode: "move" | "copy") {
  $q.dialog({
    component: MoveCopyDialog,
    componentProps: { mode, sourceColumnName: props.columnName },
  }).onOk(async (columnId: number) => {
    const ok = await (mode === "move"
      ? store.moveCardTo(props.card.id, columnId)
      : store.copyCardTo(props.card.id, columnId))
    if (ok) $q.notify({ message: mode === "move" ? "Card moved" : "Card copied" })
  })
}

const prioOptions = computed(() =>
  [
    { prio: true, label: "Mark Important", icon: "flag" },
    { prio: false, label: "Mark Not Important", icon: "outlined_flag" },
    { prio: null, label: "Remove Prio", icon: "flag_circle" },
  ].filter((o) => o.prio !== props.card.prio),
)
</script>

<template>
  <div
    class="todo-card row items-center no-wrap"
    :class="{ selected: isSelected }"
    :data-card-id="card.id"
    :style="cardStyle"
  >
    <!-- bulk mode: whole card is the select toggle -->
    <button
      v-if="store.bulkMode"
      type="button"
      class="select-overlay"
      :aria-pressed="isSelected"
      aria-label="Select card"
      @click="store.toggleSelected(card.id)"
    />
    <q-icon
      name="drag_indicator"
      class="card-handle cursor-grab q-mr-xs"
      size="xs"
    />
    <q-icon
      v-if="store.bulkMode"
      :name="isSelected ? 'check_circle' : 'radio_button_unchecked'"
      size="xs"
      class="q-mr-xs"
      aria-hidden="true"
    />
    <q-checkbox
      :model-value="isCompleted"
      dense
      color="green"
      :style="{ opacity: isCompleted ? 1 : 0.6 }"
      aria-label="Completed"
      @update:model-value="toggleCompleted"
    />
    <q-input
      v-model="title"
      class="col card-title q-ml-xs"
      :input-style="{ ...titleStyle, color: cardStyle.color }"
      borderless
      dense
      autogrow
      aria-label="Card title"
      @blur="saveTitle"
      @keydown.enter.prevent="($event.target as HTMLElement).blur()"
      @keydown.esc="revertTitle"
    />
    <template v-if="!store.bulkMode">
      <q-btn
        v-if="url"
        type="a"
        :href="url"
        target="_blank"
        rel="noopener noreferrer"
        flat
        round
        dense
        size="sm"
        icon="open_in_new"
        aria-label="Open link"
      />
      <q-btn
        v-if="card.prio === true"
        type="button"
        flat
        round
        dense
        size="sm"
        icon="flag"
        color="red"
        aria-label="Mark not important"
        @click="setPrio(false)"
      />
      <q-btn
        v-if="card.is_revive"
        type="button"
        flat
        round
        dense
        size="sm"
        icon="repeat"
        aria-label="Unset revive"
        @click="setRevive(false)"
      />
      <q-btn
        v-if="store.labels.length > 0"
        type="button"
        class="card-action"
        flat
        round
        dense
        size="sm"
        icon="label"
        aria-label="Set label"
        @click="pickLabel"
      />
      <q-btn
        type="button"
        flat
        round
        dense
        size="sm"
        icon="more_vert"
        class="card-action"
        aria-label="Card menu"
      >
        <q-menu auto-close>
          <q-list dense>
            <q-item
              clickable
              @click="setRevive(!card.is_revive)"
            >
              <q-item-section>{{ card.is_revive ? "Unset Revive" : "Set Revive" }}</q-item-section>
            </q-item>
            <q-item
              v-for="o in prioOptions"
              :key="String(o.prio)"
              clickable
              @click="setPrio(o.prio)"
            >
              <q-item-section>{{ o.label }}</q-item-section>
            </q-item>
            <q-separator />
            <q-item
              clickable
              @click="pickLabel"
            >
              <q-item-section>Set label…</q-item-section>
            </q-item>
            <q-separator />
            <q-item
              clickable
              @click="moveOrCopy('move')"
            >
              <q-item-section>Move to…</q-item-section>
            </q-item>
            <q-item
              clickable
              @click="moveOrCopy('copy')"
            >
              <q-item-section>Copy to…</q-item-section>
            </q-item>
            <q-separator />
            <q-item
              clickable
              class="text-negative"
              @click="store.removeCard(card.id)"
            >
              <q-item-section>Delete</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </template>
  </div>
</template>

<style scoped>
.todo-card {
  position: relative;
  flex-shrink: 0; /* grow with wrapped text, list scrolls instead */
  min-height: 30px;
  padding: 2px 8px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgb(0 0 0 / 20%);
}
.todo-card :deep(.q-btn:not(.text-red)),
.todo-card :deep(.q-icon) {
  color: inherit;
}
.card-title :deep(textarea) {
  font-size: 0.9rem;
}
.select-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: transparent;
  border: 0;
  border-radius: inherit;
  cursor: pointer;
}
.select-overlay:focus-visible {
  outline: 2px dashed var(--selected-outline);
}
.selected {
  outline: 2px solid var(--selected-outline);
  outline-offset: 1px;
}
/* actions only on hover/focus for mouse devices, always visible on touch */
@media (hover: hover) {
  .todo-card:not(:hover, :focus-within) .card-action {
    opacity: 0;
  }
}
</style>
