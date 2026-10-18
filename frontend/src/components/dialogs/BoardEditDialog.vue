<script setup lang="ts">
import { useDialogPluginComponent } from "quasar"
import { ref } from "vue"

import { createBoard, updateBoard } from "@/client/index.ts"
import { errorMessage } from "@/services/apiClient.ts"

const props = defineProps<{
  title: string
  /** set -> rename, unset -> create */
  boardId?: number
  name?: string
  boardKey?: string
}>()
defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK, onDialogCancel } = dialog

// eslint-disable-next-line vue/no-setup-props-reactivity-loss -- initial form value
const name = ref(props.name ?? "")
// eslint-disable-next-line vue/no-setup-props-reactivity-loss -- initial form value
const key = ref(props.boardKey ?? "")
const error = ref<string | null>(null)

async function save() {
  const n = name.value.trim()
  if (n === "") {
    error.value = "Board name is required"
    return
  }
  const k = key.value.trim() || n.toLowerCase()
  try {
    const { data } =
      props.boardId == null
        ? await createBoard({ body: { name: n, key: k } })
        : await updateBoard({ path: { board_id: props.boardId }, body: { name: n, key: k } })
    onDialogOK(data.key)
  } catch (err) {
    error.value = errorMessage(err)
  }
}
</script>

<template>
  <q-dialog
    :ref="dialog.dialogRef"
    @hide="onDialogHide"
  >
    <q-card style="min-width: 320px">
      <q-card-section class="text-h6">
        {{ title }}
      </q-card-section>
      <q-card-section>
        <q-form @submit.prevent="save">
          <q-input
            v-model="name"
            label="Board Name"
          />
          <q-input
            v-model="key"
            label="Board Key (optional)"
            hint="URL slug, default: lowercased name"
          />
          <div
            v-if="error"
            class="text-negative q-mt-sm"
          >
            {{ error }}
          </div>
          <div class="row justify-end q-gutter-sm q-mt-md">
            <q-btn
              type="button"
              flat
              label="Cancel"
              @click="onDialogCancel"
            />
            <q-btn
              type="submit"
              color="primary"
              label="Save"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>
