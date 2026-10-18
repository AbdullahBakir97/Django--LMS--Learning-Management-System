<script setup lang="ts">
import { RouterView } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'
</script>

<template>
  <div class="min-h-dvh bg-page">
    <header class="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
      <BrandMark />
      <ThemeToggle />
    </header>
    <main class="mx-auto w-full max-w-md px-4 pt-6 pb-16 sm:px-6">
      <RouterView v-slot="{ Component }">
        <div :key="$route.path" class="animate-page">
          <component :is="Component" />
        </div>
      </RouterView>
    </main>
  </div>
</template>
