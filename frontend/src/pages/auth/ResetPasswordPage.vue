<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { auth } from '@/api/auth'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

const props = defineProps<{ uid: string; token: string }>()
const form = reactive({ new_password1: '', new_password2: '' })
const errors = reactive<Record<string, string | undefined>>({})
const general = ref('')
const done = ref(false)
const busy = ref(false)

async function submit() {
  busy.value = true
  general.value = ''
  try {
    await auth.confirmPasswordReset({ uid: props.uid, token: props.token, ...form })
    done.value = true
  } catch (e) {
    if (e instanceof ApiError) {
      errors.new_password1 = e.field('new_password1')
      errors.new_password2 = e.field('new_password2')
      general.value = e.field('token') ? 'This link is invalid or has expired.' : (e.nonField ?? '')
    } else general.value = 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Choose a new password</h1>
  <template v-if="done">
    <Alert tone="success" class="mt-8">Password updated. Sign in with the new one.</Alert>
    <RouterLink class="mt-6 inline-block text-accent hover:underline" :to="{ name: 'login' }"
      >Go to sign in</RouterLink
    >
  </template>
  <form v-else class="mt-8 grid gap-5" novalidate @submit.prevent="submit">
    <Alert v-if="general" tone="danger">{{ general }}</Alert>
    <TextField
      v-model="form.new_password1"
      label="New password"
      type="password"
      autocomplete="new-password"
      :error="errors.new_password1"
      required
    />
    <TextField
      v-model="form.new_password2"
      label="Confirm new password"
      type="password"
      autocomplete="new-password"
      :error="errors.new_password2"
      required
    />
    <Button type="submit" :loading="busy">Update password</Button>
  </form>
</template>
