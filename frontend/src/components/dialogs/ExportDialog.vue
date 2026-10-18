<script setup lang="ts">
import { Notify, useDialogPluginComponent } from "quasar"
import { ref } from "vue"

import { exportBoard } from "@/client/index.ts"
import { errorMessage } from "@/services/apiClient.ts"
import { copyHtml, copyText } from "@/utils/clipboard.ts"

const props = defineProps<{ boardId: number }>()
defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK, onDialogCancel } = dialog

const completedOnly = ref(true)
const fmt = ref<"txt" | "markdown" | "html">("txt")

async function doExport() {
  try {
    const { data } = await exportBoard({
      path: { board_id: props.boardId },
      query: { fmt: fmt.value, completed_only: completedOnly.value },
    })
    await (fmt.value === "html" ? copyHtml(data.text) : copyText(data.text))
    Notify.create({ type: "positive", message: "Copied to clipboard" })
    onDialogOK()
  } catch (err) {
    Notify.create({ type: "warning", message: errorMessage(err) })
  }
}
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 300px">
      <q-card-section class="text-h6">
        Export
      </q-card-section>
      <q-card-section class="column q-gutter-md">
        <q-btn-toggle
          v-model="completedOnly"
          spread
          no-caps
          :options="[
            { label: 'Completed Only', value: true },
            { label: 'All Cards', value: false },
          ]"
        />
        <q-btn-toggle
          v-model="fmt"
          spread
          no-caps
          :options="[
            { label: 'Plain', value: 'txt' },
            { label: 'Markdown', value: 'markdown' },
            { label: 'HTML', value: 'html' },
          ]"
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
          icon="content_copy"
          label="Copy"
          @click="doExport"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
