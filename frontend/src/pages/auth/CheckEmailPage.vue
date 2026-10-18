<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { auth } from '@/api/auth'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const route = useRoute()
const email = typeof route.query.email === 'string' ? route.query.email : ''
const sent = ref(false)

async function resend() {
  await auth.resendEmail(email).catch(() => undefined)
  sent.value = true
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Check your inbox</h1>
  <p class="mt-2 text-muted">
    We sent a verification link to <span class="font-medium text-ink">{{ email || 'your email' }}</span
    >. Open it to activate your account.
  </p>
  <Alert v-if="sent" tone="success" class="mt-6">Sent again. Give it a minute.</Alert>
  <Button v-else-if="email" variant="secondary" class="mt-6" @click="resend">Resend the email</Button>
</template>
