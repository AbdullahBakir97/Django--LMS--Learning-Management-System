<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ApiError } from '@/api/client'
import { network } from '@/api/network'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'

const props = defineProps<{ username: string; name: string }>()
const emit = defineEmits<{ done: [] }>()

const form = reactive({ relationship: '', body: '' })
const errors = reactive<{ relationship?: string; body?: string }>({})
const general = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  general.value = ''
  try {
    await network.recommend(props.username, form)
    emit('done')
  } catch (e) {
    if (e instanceof ApiError) {
      errors.relationship = e.field('relationship')
      errors.body = e.field('body')
      general.value = e.nonField ?? ''
    } else general.value = 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" novalidate @submit.prevent="submit">
    <Alert v-if="general" tone="danger">{{ general }}</Alert>
    <TextField
      v-model="form.relationship"
      label="How you know them"
      :placeholder="`e.g. I managed ${name} at Acme`"
      :error="errors.relationship"
      required
    />
    <TextField
      v-model="form.body"
      label="Recommendation"
      textarea
      hint="At least 40 characters. They choose whether it shows on their profile."
      :error="errors.body"
      required
    />
    <Button type="submit" :loading="busy">Send recommendation</Button>
  </form>
</template>
