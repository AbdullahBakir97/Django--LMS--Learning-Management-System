<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhCheck, PhMapPin, PhStar, PhVideoCamera } from '@phosphor-icons/vue'
import { community, type CommunityEvent } from '@/api/community'
import { ApiError } from '@/api/client'
import { tile, when } from './format'

const props = defineProps<{ event: CommunityEvent }>()
const emit = defineEmits<{ update: [event: CommunityEvent] }>()
const busy = ref(false)
const error = ref('')
const t = computed(() => tile(props.event.starts_at))
const over = computed(() => new Date(props.event.ends_at) < new Date())
const full = computed(
  () =>
    props.event.capacity !== null &&
    props.event.going_count >= props.event.capacity &&
    props.event.my_status !== 'going',
)

async function set(status: 'going' | 'interested') {
  busy.value = true
  error.value = ''
  try {
    emit(
      'update',
      props.event.my_status === status
        ? await community.cancelRsvp(props.event.id)
        : await community.rsvp(props.event.id, status),
    )
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not save.') : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <article class="flex gap-4 rounded-lg bg-surface p-4 shadow-card ring-1 ring-line">
    <div
      class="grid h-16 w-14 shrink-0 place-content-center rounded-md text-center"
      :class="over ? 'bg-surface-2 text-muted' : 'bg-accent-soft text-accent'"
      aria-hidden="true"
    >
      <span class="font-mono text-[11px] tracking-wider">{{ t.month }}</span>
      <span class="font-display text-2xl leading-none font-semibold">{{ t.day }}</span>
    </div>
    <div class="min-w-0 flex-1">
      <RouterLink
        :to="{ name: 'event', params: { id: event.id } }"
        class="font-medium text-ink hover:underline"
        >{{ event.title }}</RouterLink
      >
      <p class="mt-0.5 text-sm text-muted">{{ when(event.starts_at, event.ends_at) }}</p>
      <p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
        <span v-if="event.location" class="inline-flex items-center gap-1"
          ><PhMapPin :size="15" weight="light" />{{ event.location }}</span
        >
        <span v-if="event.online_url" class="inline-flex items-center gap-1"
          ><PhVideoCamera :size="15" weight="light" />Online</span
        >
        <RouterLink
          v-if="event.group"
          :to="{ name: 'group', params: { slug: event.group.slug } }"
          class="hover:text-ink"
          >{{ event.group.name }}</RouterLink
        >
        <span class="font-mono text-xs"
          >{{ event.going_count }} going<template v-if="event.capacity">
            of {{ event.capacity }}</template
          ></span
        >
      </p>
      <div v-if="!over" class="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          class="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-md px-3 text-sm ring-1 transition-colors duration-quick disabled:cursor-not-allowed disabled:opacity-50"
          :class="
            event.my_status === 'going'
              ? 'bg-accent text-accent-ink ring-accent'
              : 'text-ink ring-line-strong hover:bg-surface-2'
          "
          :aria-pressed="event.my_status === 'going'"
          :disabled="busy || full"
          @click="set('going')"
        >
          <PhCheck :size="16" weight="light" /> {{ full ? 'Full' : 'Going' }}
        </button>
        <button
          type="button"
          class="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-md px-3 text-sm ring-1 transition-colors duration-quick"
          :class="
            event.my_status === 'interested'
              ? 'bg-accent-soft text-accent ring-accent/40'
              : 'text-ink ring-line-strong hover:bg-surface-2'
          "
          :aria-pressed="event.my_status === 'interested'"
          :disabled="busy"
          @click="set('interested')"
        >
          <PhStar :size="16" :weight="event.my_status === 'interested' ? 'fill' : 'light'" /> Interested
        </button>
      </div>
      <p v-if="error" class="mt-2 text-sm text-danger" role="alert">{{ error }}</p>
    </div>
  </article>
</template>
