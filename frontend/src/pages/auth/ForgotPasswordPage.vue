<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { auth } from '@/api/auth'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

const email = ref('')
const sent = ref(false)
const busy = ref(false)

async function submit() {
  busy.value = true
  await auth.requestPasswordReset(email.value).catch(() => undefined)
  busy.value = false
  sent.value = true
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Reset your password</h1>
  <p class="mt-1 text-muted">We will email you a link to choose a new one.</p>
  <Alert v-if="sent" tone="success" class="mt-8"
    >If an account exists for that address, the email is on its way.</Alert
  >
  <form v-else class="mt-8 grid gap-5" novalidate @submit.prevent="submit">
    <TextField v-model="email" label="Email" type="email" autocomplete="email" required />
    <Button type="submit" :loading="busy">Send reset link</Button>
  </form>
  <p class="mt-6 text-sm text-muted">
    <RouterLink class="hover:text-ink" :to="{ name: 'login' }">Back to sign in</RouterLink>
  </p>
</template>
