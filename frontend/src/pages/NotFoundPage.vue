<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <main class="grid min-h-dvh place-items-center bg-page px-4 text-center">
    <div>
      <p class="font-mono text-sm text-muted">404</p>
      <h1 class="mt-2 text-3xl font-semibold">That page is not here</h1>
      <RouterLink class="mt-6 inline-block text-accent hover:underline" :to="{ name: 'home' }"
        >Back home</RouterLink
      >
    </div>
  </main>
</template>
