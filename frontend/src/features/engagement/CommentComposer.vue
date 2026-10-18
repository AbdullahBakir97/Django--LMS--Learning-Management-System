<script setup lang="ts">
import { ref, useId } from 'vue'
import Button from '@/components/ui/Button.vue'

const props = withDefaults(
  defineProps<{
    label: string
    submitLabel?: string
    initial?: string
    autofocus?: boolean
    cancellable?: boolean
  }>(),
  { submitLabel: 'Post', initial: '' },
)
const emit = defineEmits<{ submit: [body: string]; cancel: [] }>()
defineExpose({ reset: () => (body.value = '') })
const body = ref(props.initial)
const id = useId()

function submit() {
  if (body.value.trim()) emit('submit', body.value.trim())
}
</script>

<template>
  <form class="grid gap-2" @submit.prevent="submit">
    <label :for="id" class="sr-only">{{ label }}</label>
    <textarea
      :id="id"
      v-model="body"
      rows="3"
      maxlength="5000"
      :placeholder="label"
      :autofocus="autofocus"
      class="w-full resize-y rounded-md bg-surface px-3 py-2 text-sm text-ink ring-1 ring-line-strong placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
      @keydown.meta.enter="submit"
      @keydown.ctrl.enter="submit"
    />
    <div class="flex items-center justify-end gap-2">
      <Button v-if="cancellable" variant="ghost" size="sm" @click="emit('cancel')">Cancel</Button>
      <Button type="submit" size="sm" :disabled="!body.trim()">{{ submitLabel }}</Button>
    </div>
  </form>
</template>
