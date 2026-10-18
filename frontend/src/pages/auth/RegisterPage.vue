<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { auth } from '@/api/auth'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

const router = useRouter()
const form = reactive({ username: '', email: '', password1: '', password2: '' })
const errors = reactive<Record<string, string | undefined>>({})
const general = ref('')
const busy = ref(false)

async function submit() {
  general.value = ''
  Object.keys(errors).forEach((k) => (errors[k] = undefined))
  busy.value = true
  try {
    await auth.register(form)
    router.push({ name: 'check-email', query: { email: form.email } })
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
  <h1 class="text-3xl font-semibold">Create your account</h1>
  <p class="mt-1 text-muted">Courses, certificates and the people who teach them.</p>
  <form class="mt-8 grid gap-5" novalidate @submit.prevent="submit">
    <Alert v-if="general" tone="danger">{{ general }}</Alert>
    <TextField
      v-model="form.username"
      label="Username"
      autocomplete="username"
      :error="errors.username"
      hint="Your public handle, shown in profile links."
      required
    />
    <TextField
      v-model="form.email"
      label="Email"
      type="email"
      autocomplete="email"
      :error="errors.email"
      required
    />
    <TextField
      v-model="form.password1"
      label="Password"
      type="password"
      autocomplete="new-password"
      :error="errors.password1"
      hint="At least 8 characters."
      required
    />
    <TextField
      v-model="form.password2"
      label="Confirm password"
      type="password"
      autocomplete="new-password"
      :error="errors.password2"
      required
    />
    <Button type="submit" :loading="busy">Create account</Button>
  </form>
  <p class="mt-6 text-sm text-muted">
    Already registered?
    <RouterLink class="text-accent hover:underline" :to="{ name: 'login' }">Sign in</RouterLink>
  </p>
</template>
