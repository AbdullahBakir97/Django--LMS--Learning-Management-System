<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

export interface Field {
  key: string
  label: string
  type?: string
  textarea?: boolean
  required?: boolean
}

const props = defineProps<{
  fields: Field[]
  initial?: Record<string, string | null>
  submit: (data: Record<string, string | null>) => Promise<unknown>
}>()
const emit = defineEmits<{ done: [] }>()

const form = reactive<Record<string, string>>(
  Object.fromEntries(props.fields.map((f) => [f.key, props.initial?.[f.key] ?? ''])),
)
const errors = reactive<Record<string, string | undefined>>({})
const general = ref('')
const busy = ref(false)
const dateKeys = new Set(props.fields.filter((f) => f.type === 'date').map((f) => f.key))

async function onSubmit() {
  busy.value = true
  general.value = ''
  try {
    const data = Object.fromEntries(
      Object.entries(form).map(([k, v]) => [k, v === '' && dateKeys.has(k) ? null : v]),
    )
    await props.submit(data)
    emit('done')
  } catch (e) {
    if (e instanceof ApiError) {
      for (const f of props.fields) errors[f.key] = e.field(f.key)
      general.value = e.nonField ?? ''
    } else general.value = 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" novalidate @submit.prevent="onSubmit">
    <Alert v-if="general" tone="danger">{{ general }}</Alert>
    <TextField
      v-for="f in fields"
      :key="f.key"
      v-model="form[f.key]"
      :label="f.label"
      :type="f.type"
      :textarea="f.textarea"
      :required="f.required"
      :error="errors[f.key]"
    />
    <div class="flex justify-end gap-2 pt-2">
      <Button type="submit" :loading="busy">Save</Button>
    </div>
  </form>
</template>
