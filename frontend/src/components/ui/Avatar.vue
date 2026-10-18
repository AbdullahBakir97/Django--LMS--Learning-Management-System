<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; src?: string | null; size?: 'sm' | 'md' | 'lg' }>(), {
  size: 'md',
})
const initials = computed(() =>
  props.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join(''),
)
const px = { sm: 'size-8 text-xs', md: 'size-10 text-sm', lg: 'size-20 text-2xl' }
</script>

<template>
  <img v-if="src" :src="src" :alt="name" class="rounded-full object-cover" :class="px[size]" />
  <span
    v-else
    class="grid place-items-center rounded-full bg-accent-soft font-display font-semibold text-accent"
    :class="px[size]"
    :aria-label="name"
    >{{ initials }}</span
  >
</template>
