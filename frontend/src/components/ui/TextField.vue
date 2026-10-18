<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    label: string
    type?: string
    autocomplete?: string
    placeholder?: string
    error?: string
    hint?: string
    required?: boolean
    textarea?: boolean
    rows?: number
  }>(),
  { type: 'text', rows: 4 },
)
const model = defineModel<string>({ default: '' })
const id = useId()
</script>

<template>
  <div class="grid gap-1.5">
    <label :for="id" class="text-sm font-medium text-ink">{{ label }}</label>
    <textarea
      v-if="textarea"
      :id="id"
      v-model="model"
      :rows="rows"
      :placeholder="placeholder"
      :required="required"
      :aria-invalid="error ? true : undefined"
      :aria-describedby="error || hint ? `${id}-help` : undefined"
      class="w-full rounded-md bg-surface px-3 py-2.5 leading-relaxed text-ink ring-1 ring-line-strong transition-shadow duration-quick placeholder:text-muted/70 focus:ring-2 focus:ring-accent focus:outline-none aria-invalid:ring-danger"
    />
    <input
      v-else
      :id="id"
      v-model="model"
      :type="type"
      :autocomplete="autocomplete"
      :placeholder="placeholder"
      :required="required"
      :aria-invalid="error ? true : undefined"
      :aria-describedby="error || hint ? `${id}-help` : undefined"
      class="h-11 w-full rounded-md bg-surface px-3 text-ink ring-1 ring-line-strong transition-shadow duration-quick placeholder:text-muted/70 focus:ring-2 focus:ring-accent focus:outline-none aria-invalid:ring-danger"
    />
    <p v-if="error" :id="`${id}-help`" class="text-sm text-danger">{{ error }}</p>
    <p v-else-if="hint" :id="`${id}-help`" class="text-sm text-muted">{{ hint }}</p>
  </div>
</template>
