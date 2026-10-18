<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; src?: string | null; size?: 'sm' | 'md' | 'lg' }>(), {
  size: 'md',
})
const px = { sm: 'size-9 text-xs', md: 'size-12 text-sm', lg: 'size-16 text-lg' }
const initials = computed(() =>
  props.name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join(''),
)
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="`${name} logo`"
    class="shrink-0 rounded-md object-cover ring-1 ring-line"
    :class="px[size]"
  />
  <span
    v-else
    aria-hidden="true"
    class="grid shrink-0 place-items-center rounded-md bg-surface-2 font-display font-semibold text-muted ring-1 ring-line"
    :class="px[size]"
    >{{ initials }}</span
  >
</template>
