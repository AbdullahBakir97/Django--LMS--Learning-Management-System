<script setup lang="ts">
import { computed, ref } from 'vue'
import { engagement, type ReactionKind, type ReactionSummary, type Target } from '@/api/engagement'
import { applyReaction, reactionKinds, total } from './reactions'

const props = defineProps<{ target: Target; summary: ReactionSummary; compact?: boolean }>()
const emit = defineEmits<{ change: [summary: ReactionSummary] }>()
const open = ref(false)

const current = computed(() => reactionKinds.find((r) => r.kind === props.summary.mine) ?? reactionKinds[0]!)
const shown = computed(() => reactionKinds.filter((r) => props.summary.counts[r.kind]))

async function pick(kind: ReactionKind | null) {
  open.value = false
  const before = props.summary
  emit('change', applyReaction(before, kind))
  try {
    emit('change', kind ? await engagement.react(props.target, kind) : await engagement.unreact(props.target))
  } catch {
    emit('change', before)
  }
}
</script>

<template>
  <div class="relative flex flex-wrap items-center gap-2" @keydown.esc="open = false">
    <div class="inline-flex overflow-hidden rounded-md ring-1 ring-line">
      <button
        type="button"
        class="inline-flex cursor-pointer items-center gap-1.5 px-2.5 text-sm transition-colors duration-quick hover:bg-surface-2"
        :class="[compact ? 'h-7' : 'h-8', summary.mine ? 'text-accent' : 'text-muted']"
        :aria-pressed="!!summary.mine"
        @click="pick(summary.mine ? null : 'like')"
      >
        <component :is="current.icon" :size="16" :weight="summary.mine ? 'fill' : 'light'" />
        {{ summary.mine ? current.label : 'Like' }}
      </button>
      <button
        type="button"
        class="cursor-pointer border-l border-line px-1.5 text-muted hover:bg-surface-2 hover:text-ink"
        :class="compact ? 'h-7' : 'h-8'"
        aria-label="Choose a reaction"
        :aria-expanded="open"
        @click="open = !open"
      >
        <span aria-hidden="true" class="text-xs">▾</span>
      </button>
    </div>
    <div
      v-if="open"
      class="absolute bottom-full left-0 z-10 mb-1 flex gap-1 rounded-lg border border-line bg-surface p-1 shadow-pop"
      role="menu"
    >
      <button
        v-for="r in reactionKinds"
        :key="r.kind"
        type="button"
        role="menuitemradio"
        :aria-checked="summary.mine === r.kind"
        class="grid size-9 cursor-pointer place-items-center rounded-md hover:bg-surface-2"
        :class="summary.mine === r.kind ? 'bg-accent-soft text-accent' : 'text-ink'"
        :title="r.label"
        :aria-label="r.label"
        @click="pick(r.kind)"
      >
        <component :is="r.icon" :size="20" weight="light" />
      </button>
    </div>
    <span v-if="total(summary)" class="inline-flex items-center gap-1 font-mono text-xs text-muted">
      <component :is="r.icon" v-for="r in shown" :key="r.kind" :size="14" weight="fill" class="text-accent" />
      {{ total(summary) }}
    </span>
  </div>
</template>
