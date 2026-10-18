<script setup lang="ts">
import { useDialogPluginComponent } from "quasar"

import { useBoardStore } from "@/stores/board.ts"

defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK } = dialog
const store = useBoardStore()
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 240px">
      <q-card-section class="text-h6">
        Set Label
      </q-card-section>
      <q-card-section class="column q-gutter-sm">
        <q-btn
          v-for="lb in store.labels"
          :key="lb.id"
          type="button"
          flat
          align="left"
          :label="lb.name"
          :style="{ borderLeft: `4px solid ${lb.color}` }"
          @click="onDialogOK(lb.id)"
        />
        <q-btn
          type="button"
          flat
          align="left"
          icon="label_off"
          label="Remove label"
          @click="onDialogOK(null)"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>
