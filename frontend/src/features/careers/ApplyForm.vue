<script setup lang="ts">
import { ref } from 'vue'
import { PhFilePdf } from '@phosphor-icons/vue'
import { careers, type Application } from '@/api/careers'
import { ApiError } from '@/api/client'
import TextField from '@/components/ui/TextField.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ jobId: number }>()
const emit = defineEmits<{ applied: [application: Application] }>()
const file = ref<File | null>(null)
const cover = ref('')
const error = ref('')
const busy = ref(false)

function pick(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] ?? null
  error.value = ''
  if (f && f.size > 5 * 1024 * 1024) {
    error.value = 'Keep the résumé under 5 MB.'
    file.value = null
    return
  }
  file.value = f
}

async function submit() {
  if (!file.value) return
  busy.value = true
  error.value = ''
  try {
    emit('applied', await careers.apply(props.jobId, file.value, cover.value))
  } catch (e) {
    error.value =
      e instanceof ApiError ? (e.field('resume') ?? e.nonField ?? 'Could not apply.') : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" @submit.prevent="submit">
    <label
      class="flex cursor-pointer items-center gap-3 rounded-md border border-dashed border-line-strong p-4 hover:bg-surface-2 focus-within:ring-2 focus-within:ring-accent"
    >
      <PhFilePdf :size="28" weight="light" class="text-muted" />
      <span class="min-w-0 flex-1 text-sm">
        <span class="block font-medium">{{ file ? file.name : 'Choose your résumé' }}</span>
        <span class="block text-muted">PDF, up to 5 MB. Only this company's hiring team can open it.</span>
      </span>
      <input type="file" accept="application/pdf,.pdf" class="sr-only" @change="pick" />
    </label>
    <TextField v-model="cover" textarea label="Cover letter" hint="Optional" />
    <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
    <div class="flex justify-end">
      <Button type="submit" :disabled="!file" :loading="busy">Send application</Button>
    </div>
  </form>
</template>
