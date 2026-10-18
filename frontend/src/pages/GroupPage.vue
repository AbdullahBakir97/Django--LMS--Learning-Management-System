<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhGear, PhLockSimple, PhPlus, PhUsersThree } from '@phosphor-icons/vue'
import { community, cursorOf, type CommunityEvent, type Group, type Member, type Post } from '@/api/community'
import { ApiError } from '@/api/client'
import { useSessionStore } from '@/stores/session'
import Alert from '@/components/ui/Alert.vue'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tag from '@/components/ui/Tag.vue'
import PostComposer from '@/features/community/PostComposer.vue'
import PostCard from '@/features/community/PostCard.vue'
import EventCard from '@/features/community/EventCard.vue'
import EventForm from '@/features/community/EventForm.vue'
import GroupForm from '@/features/community/GroupForm.vue'

const props = defineProps<{ slug: string }>()
const router = useRouter()
const session = useSessionStore()
const group = ref<Group | null>(null)
const tab = ref<'posts' | 'members' | 'events'>('posts')
const posts = ref<Post[]>([])
const next = ref<string | null>(null)
const members = ref<Member[]>([])
const pending = ref<Member[]>([])
const events = ref<CommunityEvent[]>([])
const error = ref('')
const editing = ref(false)
const planning = ref(false)
const busy = ref(false)

const isMember = computed(() => group.value?.my_status === 'active')
const canRead = computed(() => group.value?.privacy === 'public' || isMember.value)
const canManage = computed(
  () =>
    (isMember.value && ['owner', 'admin'].includes(group.value?.my_role ?? '')) ||
    session.user?.role === 'admin',
)

async function load() {
  error.value = ''
  try {
    group.value = await community.group(props.slug)
  } catch (e) {
    error.value =
      e instanceof ApiError && e.problem.status === 404 ? 'No such group.' : 'Could not load this group.'
    return
  }
  posts.value = []
  if (!canRead.value) return
  const [p, m, e] = await Promise.all([
    community.groupPosts(props.slug),
    community.members(props.slug),
    community.events({ group: props.slug }),
  ])
  posts.value = p.results
  next.value = p.next
  members.value = m
  events.value = e.results
  pending.value = canManage.value ? await community.members(props.slug, 'pending') : []
}
watch(() => props.slug, load, { immediate: true })

async function act(fn: () => Promise<Group | void>) {
  busy.value = true
  error.value = ''
  try {
    await fn()
    await load()
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Something went wrong.') : 'Network error.'
  } finally {
    busy.value = false
  }
}

async function morePosts() {
  const page = await community.groupPosts(props.slug, cursorOf(next.value))
  posts.value = [...posts.value, ...page.results]
  next.value = page.next
}

const roleLabel = (m: Member) => (m.role === 'member' ? '' : m.role)
const join = () => act(() => community.join(props.slug))
const leave = () => act(() => community.leave(props.slug))
const approve = (m: Member) => act(async () => void (await community.approve(props.slug, m.user_id)))
const removeMember = (m: Member) => act(() => community.removeMember(props.slug, m.user_id))
const toggleRole = (m: Member) =>
  act(
    async () =>
      void (await community.setRole(props.slug, m.user_id, m.role === 'admin' ? 'member' : 'admin')),
  )
const confirmingDelete = ref(false)
async function deleteGroup() {
  await community.deleteGroup(props.slug)
  router.push({ name: 'groups' })
}
</script>

<template>
  <Alert v-if="error && !group" tone="danger">{{ error }}</Alert>
  <template v-else-if="group">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0">
        <p class="flex items-center gap-2 text-sm text-muted">
          <component
            :is="group.privacy === 'private' ? PhLockSimple : PhUsersThree"
            :size="16"
            weight="light"
          />
          {{ group.privacy === 'private' ? 'Private group' : 'Public group' }} ·
          {{ group.member_count }} member{{ group.member_count === 1 ? '' : 's' }}
        </p>
        <h1 class="mt-1 text-3xl font-semibold">{{ group.name }}</h1>
        <p v-if="group.description" class="mt-2 max-w-prose whitespace-pre-line text-muted">
          {{ group.description }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button v-if="!group.my_status" :loading="busy" @click="join">
          {{ group.privacy === 'private' ? 'Ask to join' : 'Join' }}
        </Button>
        <Button
          v-else-if="group.my_status === 'pending'"
          variant="secondary"
          :loading="busy"
          title="Withdraw your request"
          @click="leave"
          >Request pending</Button
        >
        <Button v-else-if="group.my_role !== 'owner'" variant="ghost" :loading="busy" @click="leave"
          >Leave</Button
        >
        <Button v-if="canManage" variant="secondary" @click="editing = true">
          <PhGear :size="18" weight="light" /> Settings
        </Button>
      </div>
    </header>
    <Alert v-if="error" tone="danger" class="mt-4">{{ error }}</Alert>

    <Card v-if="!canRead" class="mt-10 grid justify-items-center gap-2 p-10 text-center">
      <PhLockSimple :size="28" weight="light" class="text-muted" />
      <p class="font-medium">Posts, members and events are for members.</p>
      <p class="text-sm text-muted">Ask to join and an admin will review your request.</p>
    </Card>

    <template v-else>
      <div class="mt-8 flex gap-1 border-b border-line" role="tablist">
        <button
          v-for="t in [
            { id: 'posts', label: 'Posts' },
            { id: 'members', label: `Members${pending.length ? ` · ${pending.length} waiting` : ''}` },
            { id: 'events', label: 'Events' },
          ] as const"
          :key="t.id"
          type="button"
          role="tab"
          :aria-selected="tab === t.id"
          class="-mb-px h-10 cursor-pointer border-b-2 px-3 text-sm transition-colors duration-quick"
          :class="tab === t.id ? 'border-accent text-ink' : 'border-transparent text-muted hover:text-ink'"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </div>

      <div v-if="tab === 'posts'" class="mt-6 grid max-w-2xl grid-cols-[minmax(0,1fr)] gap-4" role="tabpanel">
        <PostComposer
          v-if="isMember"
          :group-slug="slug"
          :placeholder="`Post to ${group.name}`"
          @posted="posts.unshift($event)"
        />
        <PostCard
          v-for="(p, i) in posts"
          :key="p.id"
          :post="p"
          hide-group
          @update="Object.assign(posts[i]!, $event)"
          @removed="posts.splice(i, 1)"
        />
        <p v-if="!posts.length" class="py-6 text-muted">No posts yet.</p>
        <div v-if="next" class="flex justify-center">
          <Button variant="ghost" @click="morePosts">Show older</Button>
        </div>
      </div>

      <div v-else-if="tab === 'members'" class="mt-6 grid max-w-2xl gap-6" role="tabpanel">
        <section v-if="pending.length" aria-labelledby="pending-title">
          <h2 id="pending-title" class="mb-3 font-semibold">Waiting for approval</h2>
          <Card class="divide-y divide-line">
            <div v-for="m in pending" :key="m.user_id" class="flex items-center gap-3 p-4">
              <Avatar :name="m.person.name" :src="m.person.avatar" />
              <div class="min-w-0 flex-1">
                <RouterLink
                  :to="{ name: 'profile', params: { username: m.person.username } }"
                  class="font-medium hover:underline"
                  >{{ m.person.name }}</RouterLink
                >
                <p class="truncate text-sm text-muted">{{ m.headline }}</p>
              </div>
              <Button size="sm" @click="approve(m)">Approve</Button>
              <Button size="sm" variant="ghost" @click="removeMember(m)">Decline</Button>
            </div>
          </Card>
        </section>
        <Card class="divide-y divide-line">
          <div v-for="m in members" :key="m.user_id" class="flex items-center gap-3 p-4">
            <Avatar :name="m.person.name" :src="m.person.avatar" />
            <div class="min-w-0 flex-1">
              <RouterLink
                :to="{ name: 'profile', params: { username: m.person.username } }"
                class="font-medium hover:underline"
                >{{ m.person.name }}</RouterLink
              >
              <p class="truncate text-sm text-muted">{{ m.headline }}</p>
            </div>
            <Tag v-if="roleLabel(m)">{{ roleLabel(m) }}</Tag>
            <template v-if="group.my_role === 'owner' && m.role !== 'owner'">
              <Button size="sm" variant="ghost" @click="toggleRole(m)">{{
                m.role === 'admin' ? 'Make member' : 'Make admin'
              }}</Button>
            </template>
            <Button
              v-if="canManage && m.role !== 'owner' && m.person.username !== session.user?.username"
              size="sm"
              variant="ghost"
              @click="removeMember(m)"
              >Remove</Button
            >
          </div>
        </Card>
      </div>

      <div v-else class="mt-6 grid max-w-2xl gap-4" role="tabpanel">
        <div v-if="canManage" class="flex justify-end">
          <Button variant="secondary" size="sm" @click="planning = true"
            ><PhPlus :size="16" weight="light" /> New event</Button
          >
        </div>
        <EventCard v-for="(e, i) in events" :key="e.id" :event="e" @update="events[i] = $event" />
        <p v-if="!events.length" class="py-6 text-muted">No upcoming events.</p>
      </div>
    </template>

    <Dialog v-model:open="editing" title="Group settings">
      <GroupForm
        :group="group"
        @saved="
          (g) => {
            editing = false
            g.slug !== slug ? router.push({ name: 'group', params: { slug: g.slug } }) : load()
          }
        "
      />
      <div v-if="group.my_role === 'owner'" class="mt-6 border-t border-line pt-4">
        <Button v-if="!confirmingDelete" variant="danger" size="sm" @click="confirmingDelete = true"
          >Delete group</Button
        >
        <span v-else class="inline-flex flex-wrap items-center gap-2 text-sm">
          <span class="text-muted">Delete the group, its posts and events?</span>
          <Button variant="danger" size="sm" @click="deleteGroup">Delete</Button>
          <Button variant="ghost" size="sm" @click="confirmingDelete = false">Keep</Button>
        </span>
      </div>
    </Dialog>
    <Dialog v-model:open="planning" title="New event">
      <EventForm :group-slug="slug" @created="(e) => ((planning = false), events.push(e))" />
    </Dialog>
  </template>
</template>
