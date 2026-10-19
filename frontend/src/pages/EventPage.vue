<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhArrowLeft, PhLink } from '@phosphor-icons/vue'
import { community, type CommunityEvent } from '@/api/community'
import Alert from '@/components/ui/Alert.vue'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import EventCard from '@/features/community/EventCard.vue'
import EventFeedback from '@/features/community/EventFeedback.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const event = ref<CommunityEvent | null>(null)
const missing = ref(false)
const confirming = ref(false)

watch(
  () => props.id,
  async (id) => {
    missing.value = false
    event.value = await community.event(Number(id)).catch(() => ((missing.value = true), null))
  },
  { immediate: true },
)

async function refresh() {
  event.value = await community.event(Number(props.id))
}

async function cancel() {
  await community.deleteEvent(Number(props.id))
  router.push({ name: 'events' })
}
</script>

<template>
  <div class="mx-auto grid max-w-2xl gap-6">
    <RouterLink
      :to="{ name: 'events' }"
      class="inline-flex w-fit items-center gap-1 text-sm text-muted hover:text-ink"
    >
      <PhArrowLeft :size="16" weight="light" /> Events
    </RouterLink>
    <Alert v-if="missing" tone="danger">This event is not available.</Alert>
    <template v-else-if="event">
      <h1 class="text-3xl font-semibold">{{ event.title }}</h1>
      <EventCard :event="event" @update="event = $event" />
      <Card class="grid gap-4 p-5">
        <div class="flex items-center gap-3">
          <Avatar :name="event.host.name" :src="event.host.avatar" size="sm" />
          <p class="text-sm">
            Hosted by
            <RouterLink
              :to="{ name: 'profile', params: { username: event.host.username } }"
              class="font-medium hover:underline"
              >{{ event.host.name }}</RouterLink
            >
          </p>
        </div>
        <p v-if="event.description" class="whitespace-pre-line text-ink">{{ event.description }}</p>
        <a
          v-if="event.online_url && event.my_status === 'going'"
          :href="event.online_url"
          target="_blank"
          rel="noopener"
          class="inline-flex w-fit items-center gap-1.5 text-sm text-accent hover:underline"
          ><PhLink :size="16" weight="light" /> Join online</a
        >
        <p v-else-if="event.online_url" class="text-sm text-muted">
          The online link appears once you are going.
        </p>
      </Card>
      <EventFeedback :event="event" @rated="refresh" />
      <div v-if="event.can_edit">
        <Button v-if="!confirming" variant="danger" size="sm" @click="confirming = true">Cancel event</Button>
        <span v-else class="inline-flex flex-wrap items-center gap-2 text-sm">
          <span class="text-muted">Cancel this event for everyone?</span>
          <Button variant="danger" size="sm" @click="cancel">Cancel event</Button>
          <Button variant="ghost" size="sm" @click="confirming = false">Keep it</Button>
        </span>
      </div>
    </template>
  </div>
</template>
