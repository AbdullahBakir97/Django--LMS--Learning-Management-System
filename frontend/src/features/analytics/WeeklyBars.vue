<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// One series, one hue (the accent). Bars rise from a shared baseline with 4px rounded tops.
const props = defineProps<{ weeks: { week: string; count: number }[] }>()

// Drawn at its real pixel width, so labels stay 11px on a phone instead of scaling down.
const box = ref<HTMLElement>()
const W = ref(640)
const H = 200
const pad = { top: 12, right: 8, bottom: 28, left: 32 }
const plotW = computed(() => W.value - pad.left - pad.right)
const plotH = H - pad.top - pad.bottom
let observer: ResizeObserver | undefined
onMounted(() => {
  // Resize on the next frame: changing size inside the callback loops the observer.
  observer = new ResizeObserver(([entry]) => {
    const width = Math.max(240, Math.round(entry!.contentRect.width))
    requestAnimationFrame(() => (W.value = width))
  })
  observer.observe(box.value!)
})
onBeforeUnmount(() => observer?.disconnect())

const max = computed(() => Math.max(1, ...props.weeks.map((w) => w.count)))
// A tidy top tick: 1, 2, 5, 10, 20, 50 … at or above the largest bar.
const top = computed(() => {
  const m = max.value
  const step = 10 ** Math.floor(Math.log10(m))
  return [1, 2, 5, 10].map((f) => f * step).find((t) => t >= m) ?? m
})
const ticks = computed(() => [0, top.value / 2, top.value])
const slot = computed(() => plotW.value / props.weeks.length)
const barW = computed(() => Math.max(4, slot.value - 6))
const y = (v: number) => pad.top + plotH - (v / top.value) * plotH
const day = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' })
const label = (iso: string) => day.format(new Date(`${iso}T00:00:00`))

function bar(count: number, i: number): string {
  const x = pad.left + i * slot.value + (slot.value - barW.value) / 2
  const h = Math.max(0, (count / top.value) * plotH)
  if (h === 0) return ''
  const r = Math.min(4, h, barW.value / 2)
  const yTop = pad.top + plotH - h
  const base = pad.top + plotH
  return `M${x},${base}V${yTop + r}Q${x},${yTop} ${x + r},${yTop}H${x + barW.value - r}Q${x + barW.value},${yTop} ${x + barW.value},${yTop + r}V${base}Z`
}

const hover = ref<number | null>(null)
</script>

<template>
  <div ref="box" class="relative">
    <svg :viewBox="`0 0 ${W} ${H}`" class="h-auto w-full" role="img" aria-labelledby="weekly-desc">
      <desc id="weekly-desc">
        Enrolments per week: {{ weeks.map((w) => `${label(w.week)} ${w.count}`).join(', ') }}
      </desc>
      <g v-for="t in ticks" :key="t">
        <line
          :x1="pad.left"
          :x2="W - pad.right"
          :y1="y(t)"
          :y2="y(t)"
          class="stroke-line"
          :stroke-dasharray="t === 0 ? undefined : '2 4'"
        />
        <text :x="pad.left - 8" :y="y(t) + 4" text-anchor="end" class="fill-muted font-mono text-[11px]">
          {{ t }}
        </text>
      </g>
      <g v-for="(w, i) in weeks" :key="w.week">
        <path :d="bar(w.count, i)" class="fill-accent" :class="hover === i ? 'opacity-80' : ''" />
        <text
          v-if="(weeks.length - 1 - i) % (slot < 44 ? 3 : 2) === 0"
          :x="pad.left + i * slot + slot / 2"
          :y="H - 8"
          text-anchor="middle"
          class="fill-muted font-mono text-[11px]"
        >
          {{ label(w.week) }}
        </text>
        <!-- The hit area is the whole column, wider and taller than the bar. -->
        <rect
          :x="pad.left + i * slot"
          :y="pad.top"
          :width="slot"
          :height="plotH"
          fill="transparent"
          tabindex="0"
          :aria-label="`Week of ${label(w.week)}: ${w.count} enrolments`"
          class="cursor-default outline-none"
          @mouseenter="hover = i"
          @mouseleave="hover = null"
          @focus="hover = i"
          @blur="hover = null"
        />
      </g>
    </svg>
    <div
      v-if="hover !== null"
      class="pointer-events-none absolute top-0 rounded-md bg-surface px-2.5 py-1.5 text-xs whitespace-nowrap shadow-pop ring-1 ring-line"
      :style="{
        left: `${Math.min(W - 70, Math.max(70, pad.left + hover * slot + slot / 2))}px`,
        transform: 'translateX(-50%)',
      }"
      role="status"
    >
      <span class="text-muted">Week of {{ label(weeks[hover]!.week) }}</span>
      <span class="ml-2 font-semibold text-ink tabular-nums">{{ weeks[hover]!.count }}</span>
    </div>
  </div>
</template>
