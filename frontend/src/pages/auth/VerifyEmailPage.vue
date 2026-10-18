<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { auth } from '@/api/auth'
import Alert from '@/components/ui/Alert.vue'

const props = defineProps<{ code: string }>()
const state = ref<'working' | 'done' | 'failed'>('working')

onMounted(async () => {
  try {
    await auth.verifyEmail(props.code)
    state.value = 'done'
  } catch {
    state.value = 'failed'
  }
})
</script>

<template>
  <h1 class="text-3xl font-semibold">Email verification</h1>
  <p v-if="state === 'working'" class="mt-2 text-muted">Confirming your address…</p>
  <template v-else-if="state === 'done'">
    <Alert tone="success" class="mt-6">Your email is verified. You can sign in now.</Alert>
    <RouterLink class="mt-6 inline-block text-accent hover:underline" :to="{ name: 'login' }"
      >Go to sign in</RouterLink
    >
  </template>
  <template v-else>
    <Alert tone="danger" class="mt-6">This link is invalid or has expired.</Alert>
    <RouterLink class="mt-6 inline-block text-accent hover:underline" :to="{ name: 'register' }"
      >Register again</RouterLink
    >
  </template>
</template>
