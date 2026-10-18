<script setup lang="ts">
import { computed } from 'vue'
import { PhCalendarPlus, PhVideoCamera, PhPhone, PhBuildings } from '@phosphor-icons/vue'
import { apiBlob } from '@/api/client'
import { labels, type Interview } from '@/api/careers'
import Tag from '@/components/ui/Tag.vue'

const props = defineProps<{ interview: Interview }>()
const icon = { video: PhVideoCamera, phone: PhPhone, onsite: PhBuildings }
const when = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})
const cancelled = computed(() => props.interview.status === 'cancelled')
const tone = computed(
  () =>
    ({
      confirmed: '!bg-success-soft !text-success',
      declined: '!bg-danger-soft !text-danger',
      scheduled: '!bg-accent-soft !text-accent',
      cancelled: '',
    })[props.interview.status],
)

async function addToCalendar() {
  const url = URL.createObjectURL(await apiBlob(props.interview.calendar_url))
  const link = Object.assign(document.createElement('a'), {
    href: url,
    download: `interview-${props.interview.id}.ics`,
  })
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
</script>

<template>
  <div class="grid gap-2 rounded-md bg-surface-2 p-3" :class="{ 'opacity-60': cancelled }">
    <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
      <component :is="icon[interview.kind]" :size="18" weight="light" aria-hidden="true" />
      <span class="font-medium" :class="{ 'line-through': cancelled }">
        {{ when.format(new Date(interview.starts_at)) }}
      </span>
      <span class="font-mono text-xs text-muted"
        >{{ interview.duration_minutes }} min · {{ labels.interview[interview.kind] }}</span
      >
      <Tag :class="tone">{{ interview.status_label }}</Tag>
    </div>
    <template v-if="!cancelled">
      <a
        v-if="/^https?:\/\//.test(interview.location)"
        :href="interview.location"
        target="_blank"
        rel="noopener"
        class="truncate text-sm text-accent hover:underline"
        >{{ interview.location }}</a
      >
      <p v-else class="text-sm">{{ interview.location }}</p>
      <p v-if="interview.details" class="text-sm whitespace-pre-line text-ink/80">{{ interview.details }}</p>
      <p v-if="interview.response_note" class="text-sm text-muted">“{{ interview.response_note }}”</p>
    </template>
    <div class="flex flex-wrap items-center gap-2">
      <slot />
      <button
        v-if="!cancelled"
        type="button"
        class="inline-flex h-8 cursor-pointer items-center gap-1 rounded-md px-2 text-sm text-muted hover:bg-surface hover:text-ink"
        @click="addToCalendar"
      >
        <PhCalendarPlus :size="16" weight="light" /> Add to calendar
      </button>
    </div>
  </div>
</template>
