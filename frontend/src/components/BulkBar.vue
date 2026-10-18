<script setup lang="ts">
import { useBoardStore } from "@/stores/board.ts"
import { contrastColor } from "@/utils/color.ts"

const store = useBoardStore()
const unsetStyle = { background: "rgb(255 255 255 / 25%)" }
</script>

<template>
  <div class="row items-center q-gutter-sm q-mb-md text-white">
    <span>Select cards, then:</span>
    <q-btn
      type="button"
      dense
      no-caps
      icon="repeat"
      label="Set repeat"
      @click="store.bulkUpdate({ is_repeat: true })"
    />
    <q-btn
      type="button"
      dense
      no-caps
      label="Unset repeat"
      :style="unsetStyle"
      @click="store.bulkUpdate({ is_repeat: false })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="flag"
      color="red"
      aria-label="Mark Important"
      @click="store.bulkUpdate({ prio: true })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="outlined_flag"
      aria-label="Mark Not Important"
      @click="store.bulkUpdate({ prio: false })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="flag_circle"
      aria-label="Remove Prio"
      :style="unsetStyle"
      @click="store.bulkUpdate({ prio: null })"
    />
    <q-btn
      v-for="lb in store.labels"
      :key="lb.id"
      type="button"
      dense
      no-caps
      :label="lb.name"
      :style="{ background: lb.color, color: contrastColor(lb.color), borderRadius: '16px' }"
      @click="store.bulkUpdate({ label_id: lb.id })"
    />
    <q-btn
      type="button"
      dense
      round
      icon="label_off"
      aria-label="Remove label"
      :style="unsetStyle"
      @click="store.bulkUpdate({ label_id: null })"
    />
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
