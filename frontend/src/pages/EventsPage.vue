<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhCalendarBlank, PhPlus } from '@phosphor-icons/vue'
import { community, type CommunityEvent } from '@/api/community'
import Button from '@/components/ui/Button.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EventCard from '@/features/community/EventCard.vue'
import EventForm from '@/features/community/EventForm.vue'

type View = 'upcoming' | 'attending' | 'past'
const view = ref<View>('upcoming')
const events = ref<CommunityEvent[]>([])
const loaded = ref(false)
const planning = ref(false)

watch(
  view,
  async (v) => {
    loaded.value = false
    events.value = (
      await community.events({ when: v === 'past' ? 'past' : 'upcoming', attending: v === 'attending' })
    ).results
    loaded.value = true
  },
  { immediate: true },
)
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Events</h1>
      <p class="mt-1 text-muted">Meetups, office hours and study sessions.</p>
    </div>
    <Button @click="planning = true"><PhPlus :size="18" weight="light" /> New event</Button>
  </div>

  <div class="mt-6 flex w-fit rounded-md bg-surface-2 p-1 text-sm" role="group" aria-label="Show">
    <button
      v-for="opt in [
        { v: 'upcoming', label: 'Upcoming' },
        { v: 'attending', label: 'Your RSVPs' },
        { v: 'past', label: 'Past' },
      ] as const"
      :key="opt.v"
      type="button"
      class="h-8 cursor-pointer rounded-sm px-3 transition-colors duration-quick"
      :class="view === opt.v ? 'bg-surface text-ink shadow-card' : 'text-muted hover:text-ink'"
      :aria-pressed="view === opt.v"
      @click="view = opt.v"
    >
      {{ opt.label }}
    </button>
  </div>

  <div class="mt-6 grid max-w-3xl gap-3">
    <EventCard v-for="(e, i) in events" :key="e.id" :event="e" @update="events[i] = $event" />
    <div v-if="loaded && !events.length" class="grid justify-items-center gap-2 py-12 text-center text-muted">
      <PhCalendarBlank :size="28" weight="light" />
      {{
        view === 'past'
          ? 'No past events.'
          : view === 'attending'
            ? 'You have not RSVPed to anything.'
            : 'Nothing scheduled. Plan one.'
      }}
    </div>
  </div>

  <Dialog v-model:open="planning" title="New event">
    <EventForm @created="(e) => ((planning = false), events.unshift(e))" />
  </Dialog>
</template>
