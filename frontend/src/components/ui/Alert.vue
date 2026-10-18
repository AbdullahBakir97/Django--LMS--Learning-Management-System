<script setup lang="ts">
withDefaults(defineProps<{ tone?: 'danger' | 'success' | 'info' }>(), { tone: 'info' })
</script>

<template>
  <div
    role="alert"
    class="rounded-md px-3.5 py-3 text-sm"
    :class="{
      'bg-danger-soft text-danger': tone === 'danger',
      'bg-success-soft text-success': tone === 'success',
      'bg-surface-2 text-ink': tone === 'info',
    }"
  >
    <slot />
  </div>
</template>
