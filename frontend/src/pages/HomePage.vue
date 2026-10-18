<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhLockSimple, PhUsersThree } from '@phosphor-icons/vue'
import { community, cursorOf, type CommunityEvent, type Group, type Post } from '@/api/community'
import { useSessionStore } from '@/stores/session'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Alert from '@/components/ui/Alert.vue'
import PostComposer from '@/features/community/PostComposer.vue'
import PostCard from '@/features/community/PostCard.vue'
import EventCard from '@/features/community/EventCard.vue'

const session = useSessionStore()
const posts = ref<Post[]>([])
const next = ref<string | null>(null)
const groups = ref<Group[]>([])
const events = ref<CommunityEvent[]>([])
const loaded = ref(false)

const failed = ref(false)

onMounted(async () => {
  try {
    const [feed, mine, upcoming] = await Promise.all([
      community.feed(),
      community.groups({ mine: true }),
      community.events({ when: 'upcoming' }),
    ])
    posts.value = feed.results
    next.value = feed.next
    groups.value = mine.results.filter((g) => g.my_status === 'active')
    events.value = upcoming.results.slice(0, 3)
    loaded.value = true
  } catch {
    failed.value = true
  }
})

async function more() {
  const page = await community.feed(cursorOf(next.value))
  posts.value = [...posts.value, ...page.results]
  next.value = page.next
}
</script>

<template>
  <div class="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
    <div class="grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-4">
      <h1 class="text-3xl font-semibold">Hello, {{ session.user?.first_name || session.user?.username }}</h1>
      <PostComposer :groups="groups" @posted="posts.unshift($event)" />
      <Alert v-if="failed" tone="danger">Your feed did not load. Check your connection and reload.</Alert>
      <PostCard
        v-for="(p, i) in posts"
        :key="p.id"
        :post="p"
        @update="Object.assign(posts[i]!, $event)"
        @removed="posts.splice(i, 1)"
      />
      <Card v-if="loaded && !posts.length" class="p-6 text-center">
        <p class="font-medium">Your feed is quiet.</p>
        <p class="mt-1 text-sm text-muted">
          Posts from people you follow or are connected with, and from your groups, show up here.
        </p>
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <RouterLink :to="{ name: 'network' }"
            ><Button variant="secondary" size="sm">Find people</Button></RouterLink
          >
          <RouterLink :to="{ name: 'groups' }"
            ><Button variant="secondary" size="sm">Browse groups</Button></RouterLink
          >
        </div>
      </Card>
      <div v-if="next" class="flex justify-center">
        <Button variant="ghost" @click="more">Show older posts</Button>
      </div>
    </div>

    <aside class="grid min-w-0 content-start gap-8">
      <section aria-labelledby="events-title">
        <div class="mb-3 flex items-baseline justify-between">
          <h2 id="events-title" class="font-semibold">Upcoming events</h2>
          <RouterLink :to="{ name: 'events' }" class="text-sm text-accent hover:underline">All</RouterLink>
        </div>
        <div class="grid gap-3">
          <EventCard v-for="(e, i) in events" :key="e.id" :event="e" @update="events[i] = $event" />
          <p v-if="loaded && !events.length" class="text-sm text-muted">Nothing scheduled yet.</p>
        </div>
      </section>
      <section aria-labelledby="groups-title">
        <div class="mb-3 flex items-baseline justify-between">
          <h2 id="groups-title" class="font-semibold">Your groups</h2>
          <RouterLink :to="{ name: 'groups' }" class="text-sm text-accent hover:underline">Browse</RouterLink>
        </div>
        <ul class="grid gap-1">
          <li v-for="g in groups" :key="g.slug">
            <RouterLink
              :to="{ name: 'group', params: { slug: g.slug } }"
              class="flex items-center gap-2 rounded-md px-2 py-2 text-sm hover:bg-surface-2"
            >
              <component
                :is="g.privacy === 'private' ? PhLockSimple : PhUsersThree"
                :size="18"
                weight="light"
                class="text-muted"
              />
              <span class="min-w-0 flex-1 truncate">{{ g.name }}</span>
              <span class="font-mono text-xs text-muted">{{ g.member_count }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-if="loaded && !groups.length" class="text-sm text-muted">You have not joined a group yet.</p>
      </section>
    </aside>
  </div>
</template>
