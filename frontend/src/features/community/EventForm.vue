<script setup lang="ts">
import { reactive, ref } from 'vue'
import { community, type CommunityEvent } from '@/api/community'
import { ApiError } from '@/api/client'
import TextField from '@/components/ui/TextField.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'
import { localInput } from './format'

const props = defineProps<{ groupSlug?: string }>()
const emit = defineEmits<{ created: [event: CommunityEvent] }>()
const start = new Date(Date.now() + 86_400_000)
start.setMinutes(0, 0, 0)
const form = reactive({
  title: '',
  description: '',
  starts_at: localInput(start),
  ends_at: localInput(new Date(start.getTime() + 2 * 3_600_000)),
  location: '',
  online_url: '',
  capacity: '',
})
const errors = ref<ApiError | null>(null)
const busy = ref(false)

async function submit() {
  busy.value = true
  errors.value = null
  try {
    emit(
      'created',
      await community.createEvent({
        ...form,
        starts_at: new Date(form.starts_at).toISOString(),
        ends_at: new Date(form.ends_at).toISOString(),
        capacity: form.capacity ? Number(form.capacity) : null,
        group_slug: props.groupSlug ?? null,
      }),
    )
  } catch (e) {
    if (e instanceof ApiError) errors.value = e
    else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" @submit.prevent="submit">
    <TextField v-model="form.title" label="Title" required :error="errors?.field('title')" />
    <div class="grid gap-4 sm:grid-cols-2">
      <TextField
        v-model="form.starts_at"
        type="datetime-local"
        label="Starts"
        required
        :error="errors?.field('starts_at')"
      />
      <TextField
        v-model="form.ends_at"
        type="datetime-local"
        label="Ends"
        required
        :error="errors?.field('ends_at')"
      />
    </div>
    <TextField
      v-model="form.location"
      label="Place"
      hint="Or give an online link below"
      :error="errors?.field('location')"
    />
    <TextField
      v-model="form.online_url"
      type="url"
      label="Online link"
      :error="errors?.field('online_url')"
    />
    <TextField v-model="form.capacity" type="number" label="Capacity" hint="Leave empty for no limit" />
    <TextField v-model="form.description" textarea label="Description" />
    <Alert
      v-if="errors?.problem.errors?.non_field_errors || (errors && !errors.problem.errors)"
      tone="danger"
      >{{ errors?.nonField }}</Alert
    >
    <div class="flex justify-end"><Button type="submit" :loading="busy">Create event</Button></div>
  </form>
</template>
