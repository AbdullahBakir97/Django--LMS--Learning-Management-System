<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ done: number; total: number }>()
const pct = computed(() => (props.total ? Math.round((100 * props.done) / props.total) : 0))
</script>

<template>
  <div class="grid gap-1.5">
    <div class="flex justify-between font-mono text-xs text-muted">
      <span>{{ done }} of {{ total }} lessons</span><span>{{ pct }}%</span>
    </div>
    <div
      class="h-1.5 overflow-hidden rounded-full bg-surface-2"
      role="progressbar"
      :aria-valuenow="pct"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div
        class="h-full rounded-full bg-accent transition-[width] duration-base ease-out"
        :style="{ width: `${pct}%` }"
      />
    </div>
  </div>
</template>
