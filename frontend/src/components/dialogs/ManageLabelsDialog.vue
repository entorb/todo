<script setup lang="ts">
import { useDialogPluginComponent, useQuasar } from "quasar"

import { deleteLabel, type LabelPublic } from "@/client/index.ts"
import LabelEditorDialog from "@/components/dialogs/LabelEditorDialog.vue"
import { useBoardStore } from "@/stores/board.ts"

defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK } = dialog
const $q = useQuasar()
const store = useBoardStore()

function edit(label?: LabelPublic) {
  $q.dialog({ component: LabelEditorDialog, componentProps: { label } }).onOk(() =>
    store.loadLabels(),
  )
}

function remove(label: LabelPublic) {
  $q.dialog({
    title: "Delete label",
    message: `Delete label '${label.name}'? It is removed from all cards on all boards.`,
    cancel: true,
    ok: { color: "negative", label: "Delete" },
  }).onOk(async () => {
    await store.run(() => deleteLabel({ path: { label_id: label.id } }))
    await store.loadLabels()
  })
}
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 300px">
      <q-card-section class="text-h6">
        Manage Labels
      </q-card-section>
      <q-list>
        <q-item
          v-for="lb in store.labels"
          :key="lb.id"
        >
          <q-item-section avatar>
            <q-icon
              name="circle"
              :style="{ color: lb.color }"
            />
          </q-item-section>
          <q-item-section>{{ lb.name }}</q-item-section>
          <q-item-section side>
            <div class="row no-wrap">
              <q-btn
                type="button"
                flat
                round
                dense
                icon="edit"
                aria-label="Edit label"
                @click="edit(lb)"
              />
              <q-btn
                type="button"
                flat
                round
                dense
                icon="delete"
                aria-label="Delete label"
                @click="remove(lb)"
              />
            </div>
          </q-item-section>
        </q-item>
      </q-list>
      <q-card-actions align="right">
        <q-btn
          type="button"
          flat
          color="primary"
          label="Create New Label"
          @click="edit()"
        />
        <q-btn
          type="button"
          flat
          label="Close"
          @click="onDialogOK"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
