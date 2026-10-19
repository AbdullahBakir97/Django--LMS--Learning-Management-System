<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhStar } from '@phosphor-icons/vue'
import { community, type CommunityEvent, type EventFeedback } from '@/api/community'
import { ApiError } from '@/api/client'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'

const props = defineProps<{ event: CommunityEvent }>()
const emit = defineEmits<{ rated: [] }>()

const over = computed(() => new Date(props.event.ends_at) <= new Date())
const canRate = computed(() => over.value && props.event.my_status === 'going')
const rating = ref(props.event.my_rating ?? 0)
const comment = ref('')
const saved = ref(false)
const error = ref('')
const comments = ref<EventFeedback[]>([])

onMounted(async () => {
  if (over.value && props.event.can_edit) comments.value = await community.eventFeedback(props.event.id)
})

async function save() {
  error.value = ''
  try {
    await community.rateEvent(props.event.id, rating.value, comment.value.trim())
    saved.value = true
    emit('rated')
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not save.') : 'Network error.'
  }
}
</script>

<template>
  <Card v-if="over" class="grid gap-4 p-5">
    <div class="flex flex-wrap items-baseline justify-between gap-2">
      <h2 class="text-lg font-semibold">How it went</h2>
      <p v-if="event.rating_count" class="text-sm text-muted">
        <span class="font-semibold text-ink">{{ event.rating?.toFixed(1) }}</span> out of 5 ·
        {{ event.rating_count }} rating{{ event.rating_count === 1 ? '' : 's' }}
      </p>
      <p v-else class="text-sm text-muted">No ratings yet.</p>
    </div>

    <form v-if="canRate" class="grid gap-3" @submit.prevent="save">
      <fieldset class="grid gap-2">
        <legend class="mb-2 text-sm font-medium">
          {{ event.my_rating ? 'Your rating' : 'You went. How was it?' }}
        </legend>
        <div class="flex gap-1">
          <label v-for="n in 5" :key="n" class="cursor-pointer">
            <input v-model="rating" type="radio" name="rating" :value="n" class="peer sr-only" />
            <PhStar
              :size="28"
              :weight="n <= rating ? 'fill' : 'light'"
              :class="n <= rating ? 'text-accent' : 'text-muted'"
              class="rounded-sm peer-focus-visible:ring-2 peer-focus-visible:ring-accent"
            />
            <span class="sr-only">{{ n }} out of 5</span>
          </label>
        </div>
      </fieldset>
      <label class="grid gap-1.5 text-sm font-medium">
        A note for the host (optional)
        <textarea
          v-model="comment"
          rows="2"
          maxlength="2000"
          class="w-full resize-y rounded-md bg-page px-3 py-2 font-normal text-ink ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
        />
      </label>
      <div class="flex items-center gap-3">
        <Button type="submit" size="sm" :disabled="!rating">Save rating</Button>
        <span v-if="saved" class="text-sm text-success" role="status">Thanks, saved.</span>
        <span v-if="error" class="text-sm text-danger" role="alert">{{ error }}</span>
      </div>
    </form>

    <div v-if="event.can_edit && comments.length" class="grid gap-3 border-t border-line pt-4">
      <h3 class="text-sm font-medium">What people said</h3>
      <ul class="grid gap-3">
        <li v-for="c in comments" :key="c.person.username" class="flex items-start gap-3">
          <Avatar :name="c.person.name" :src="c.person.avatar" size="sm" />
          <div class="min-w-0">
            <p class="text-sm">
              <span class="font-medium">{{ c.person.name }}</span>
              <span class="ml-2 font-mono text-xs text-muted">{{ c.rating }}/5</span>
            </p>
            <p v-if="c.comment" class="text-sm whitespace-pre-line text-ink/90">{{ c.comment }}</p>
          </div>
        </li>
      </ul>
    </div>
  </Card>
</template>
