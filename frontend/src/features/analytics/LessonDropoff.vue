<script setup lang="ts">
import type { CourseAnalytics } from '@/api/learning'

// Read as a list: each lesson's bar is the share of everyone enrolled who finished it, so the
// steepest step down is where learners stop.
const props = defineProps<{ lessons: CourseAnalytics['lessons']; enrolled: number }>()
const pct = (n: number) => (props.enrolled ? Math.round((100 * n) / props.enrolled) : 0)
</script>

<template>
  <ol class="grid gap-3">
    <li v-for="(l, i) in lessons" :key="l.id" class="grid gap-1">
      <div class="flex items-baseline justify-between gap-3 text-sm">
        <span class="min-w-0 truncate"
          ><span class="font-mono text-xs text-muted">{{ l.order }}.</span> {{ l.title }}</span
        >
        <span class="shrink-0 tabular-nums">
          <span class="font-semibold">{{ pct(l.completed) }}%</span>
          <span class="text-muted"> · {{ l.completed }}</span>
        </span>
      </div>
      <div class="h-2 rounded-full bg-surface-2" aria-hidden="true">
        <div class="h-2 rounded-full bg-accent" :style="{ width: `${pct(l.completed)}%` }" />
      </div>
      <p v-if="i > 0 && lessons[i - 1]!.completed - l.completed > 0" class="font-mono text-xs text-muted">
        {{ lessons[i - 1]!.completed - l.completed }} stopped before this lesson
      </p>
    </li>
  </ol>
</template>
