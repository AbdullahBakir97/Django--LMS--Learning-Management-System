<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { useSessionStore } from '@/stores/session'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

const session = useSessionStore()
const router = useRouter()
const route = useRoute()
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await session.login(email.value, password.value)
    router.push(typeof route.query.next === 'string' ? route.query.next : { name: 'home' })
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not sign in.') : 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Welcome back</h1>
  <p class="mt-1 text-muted">Sign in to keep learning.</p>
  <form class="mt-8 grid gap-5" novalidate @submit.prevent="submit">
    <Alert v-if="error" tone="danger">{{ error }}</Alert>
    <TextField v-model="email" label="Email" type="email" autocomplete="email" required />
    <TextField v-model="password" label="Password" type="password" autocomplete="current-password" required />
    <Button type="submit" :loading="busy">Sign in</Button>
  </form>
  <p class="mt-6 flex justify-between text-sm text-muted">
    <RouterLink class="hover:text-ink" :to="{ name: 'forgot-password' }">Forgot password?</RouterLink>
    <RouterLink class="text-accent hover:underline" :to="{ name: 'register' }">Create an account</RouterLink>
  </p>
</template>
