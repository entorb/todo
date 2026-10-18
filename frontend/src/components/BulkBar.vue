<script setup lang="ts">
import { computed } from "vue"

import { useBoardStore } from "@/stores/board.ts"
import { contrastColor } from "@/utils/color.ts"

const store = useBoardStore()
const unsetStyle = { background: "rgb(255 255 255 / 25%)" }
const none = computed(() => store.selected.size === 0)
</script>

<template>
  <div class="row items-center q-gutter-sm q-mb-md text-white">
    <span>{{ none ? "Select cards, then:" : `${store.selected.size} selected:` }}</span>
    <q-btn
      type="button"
      dense
      no-caps
      icon="repeat"
      label="Set repeat"
      :disable="none"
      @click="store.bulkUpdate({ is_repeat: true })"
    />
    <q-btn
      type="button"
      dense
      no-caps
      label="Unset repeat"
      :style="unsetStyle"
      :disable="none"
      @click="store.bulkUpdate({ is_repeat: false })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="flag"
      color="red"
      aria-label="Mark Important"
      :disable="none"
      @click="store.bulkUpdate({ prio: true })"
    >
      <q-tooltip>Mark Important</q-tooltip>
    </q-btn>
    <q-btn
      type="button"
      dense
      round
      icon="outlined_flag"
      aria-label="Mark Not Important"
      :disable="none"
      @click="store.bulkUpdate({ prio: false })"
    >
      <q-tooltip>Mark Not Important</q-tooltip>
    </q-btn>
    <q-btn
      type="button"
      dense
      round
      icon="flag_circle"
      aria-label="Remove Prio"
      :style="unsetStyle"
      :disable="none"
      @click="store.bulkUpdate({ prio: null })"
    >
      <q-tooltip>Remove Prio</q-tooltip>
    </q-btn>
    <q-btn
      v-for="lb in store.labels"
      :key="lb.id"
      type="button"
      dense
      no-caps
      :label="lb.name"
      :style="{ background: lb.color, color: contrastColor(lb.color), borderRadius: '16px' }"
      :disable="none"
      @click="store.bulkUpdate({ label_id: lb.id })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="label_off"
      aria-label="Remove label"
      :style="unsetStyle"
      :disable="none"
      @click="store.bulkUpdate({ label_id: null })"
    >
      <q-tooltip>Remove label</q-tooltip>
    </q-btn>
    <q-btn
      type="button"
      dense
      round
      flat
      icon="close"
      aria-label="Cancel bulk edit"
      @click="store.exitBulk()"
    />
  </div>
</template>
