<script setup lang="ts">
import { PhMoon, PhSun } from '@phosphor-icons/vue'
import { theme, toggleTheme } from '@/composables/useTheme'
</script>

<template>
  <button
    type="button"
    class="grid size-10 cursor-pointer place-items-center rounded-md text-muted transition-colors duration-quick hover:bg-surface-2 hover:text-ink"
    :aria-label="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
    @click="toggleTheme"
  >
    <PhSun v-if="theme === 'dark'" :size="20" weight="light" />
    <PhMoon v-else :size="20" weight="light" />
  </button>
</template>
