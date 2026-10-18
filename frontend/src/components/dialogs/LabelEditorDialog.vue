<script setup lang="ts">
import { useDialogPluginComponent } from "quasar"
import { ref } from "vue"

import { createLabel, type LabelPublic, updateLabel } from "@/client/index.ts"
import { errorMessage } from "@/services/apiClient.ts"

const props = defineProps<{ label?: LabelPublic }>()
defineEmits<{ ok: [payload?: unknown]; hide: [] }>()
const dialog = useDialogPluginComponent()
const { onDialogHide, onDialogOK, onDialogCancel } = dialog

// eslint-disable-next-line vue/no-setup-props-reactivity-loss -- initial form value
const name = ref(props.label?.name ?? "")
// eslint-disable-next-line vue/no-setup-props-reactivity-loss -- initial form value
const color = ref(props.label?.color ?? "#cccccc")
const error = ref<string | null>(null)

async function save() {
  const n = name.value.trim()
  if (n === "") {
    error.value = "Label name is required"
    return
  }
  const c = color.value.toLowerCase().startsWith("#") ? color.value.toLowerCase() : "#cccccc"
  const body = { name: n, color: c }
  try {
    await (props.label == null
      ? createLabel({ body })
      : updateLabel({ path: { label_id: props.label.id }, body }))
    onDialogOK()
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
    <q-card style="min-width: 300px">
      <q-card-section class="text-h6">
        {{ label == null ? "Create Label" : "Edit Label" }}
      </q-card-section>
      <q-card-section>
        <q-form @submit.prevent="save">
          <q-input
            v-model="name"
            label="Name"
          />
          <q-input
            v-model="color"
            label="Color"
          >
            <template #append>
              <q-icon
                name="colorize"
                class="cursor-pointer"
                :style="{ color }"
              >
                <q-popup-proxy>
                  <q-color
                    v-model="color"
                    format-model="hex"
                    no-header-tabs
                  />
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
          <div
            v-if="error"
            class="text-negative q-mt-sm"
          >
            {{ error }}
          </div>
        </q-form>
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
          label="Save"
          @click="save"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
