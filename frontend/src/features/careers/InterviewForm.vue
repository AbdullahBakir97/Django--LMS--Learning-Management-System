<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ApiError } from '@/api/client'
import { careers, labels, type Interview, type InterviewKind } from '@/api/careers'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'

const props = defineProps<{ applicationId: number }>()
const emit = defineEmits<{ done: [interview: Interview] }>()

const form = reactive({
  starts_at: '',
  duration_minutes: 45,
  kind: 'video' as InterviewKind,
  location: '',
  details: '',
})
const errors = reactive<Record<string, string | undefined>>({})
const general = ref('')
const busy = ref(false)
const select =
  'h-11 rounded-md bg-surface px-3 text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none'

async function submit() {
  busy.value = true
  general.value = ''
  try {
    // datetime-local is the viewer's local time; the API stores an instant.
    const starts_at = form.starts_at ? new Date(form.starts_at).toISOString() : ''
    emit('done', await careers.scheduleInterview(props.applicationId, { ...form, starts_at }))
  } catch (e) {
    if (e instanceof ApiError) {
      for (const k of Object.keys(form)) errors[k] = e.field(k)
      general.value = e.nonField ?? ''
    } else general.value = 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
    <Alert v-if="general" tone="danger" class="sm:col-span-2">{{ general }}</Alert>
    <TextField
      v-model="form.starts_at"
      label="Date and time"
      type="datetime-local"
      :error="errors.starts_at"
      hint="In your time zone. The candidate sees it in theirs."
      required
      class="sm:col-span-2"
    />
    <label class="grid gap-1.5 text-sm font-medium">
      Length
      <select v-model.number="form.duration_minutes" :class="select">
        <option v-for="m in [30, 45, 60, 90, 120]" :key="m" :value="m">{{ m }} minutes</option>
      </select>
    </label>
    <label class="grid gap-1.5 text-sm font-medium">
      Format
      <select v-model="form.kind" :class="select">
        <option v-for="(label, k) in labels.interview" :key="k" :value="k">{{ label }}</option>
      </select>
    </label>
    <TextField
      v-model="form.location"
      :label="form.kind === 'video' ? 'Meeting link' : form.kind === 'phone' ? 'Phone number' : 'Address'"
      :error="errors.location"
      required
      class="sm:col-span-2"
    />
    <TextField
      v-model="form.details"
      label="Notes for the candidate"
      textarea
      hint="Who they will meet, what to prepare."
      :error="errors.details"
      class="sm:col-span-2"
    />
    <Button type="submit" :loading="busy" class="sm:col-span-2">Send invitation</Button>
  </form>
</template>
