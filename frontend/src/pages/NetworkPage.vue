<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhUsersThree } from '@phosphor-icons/vue'
import { network, type Connection, type FollowRow, type Suggestion } from '@/api/network'
import { useSessionStore } from '@/stores/session'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PersonCard from '@/features/network/PersonCard.vue'

const session = useSessionStore()
type Tab = 'connections' | 'followers' | 'following'
const tab = ref<Tab>('connections')
const incoming = ref<Connection[]>([])
const outgoing = ref<Connection[]>([])
const connections = ref<Connection[]>([])
const followers = ref<FollowRow[]>([])
const following = ref<FollowRow[]>([])
const suggestions = ref<Suggestion[]>([])
const asked = ref(new Set<string>())
const loaded = ref(false)

async function load() {
  const me = session.user!.username
  const [i, o, c, fs, fg, s] = await Promise.all([
    network.connections('incoming'),
    network.connections('outgoing'),
    network.connections('accepted'),
    network.followers(me),
    network.following(me),
    network.suggestions(),
  ])
  incoming.value = i.results
  outgoing.value = o.results
  connections.value = c.results
  followers.value = fs.results
  following.value = fg.results
  suggestions.value = s
  loaded.value = true
}
onMounted(load)

const tabs = computed(() => [
  { id: 'connections' as Tab, label: 'Connections', count: connections.value.length },
  { id: 'followers' as Tab, label: 'Followers', count: followers.value.length },
  { id: 'following' as Tab, label: 'Following', count: following.value.length },
])

async function accept(c: Connection) {
  await network.accept(c.id)
  await load()
}
async function decline(c: Connection) {
  await network.decline(c.id)
  incoming.value = incoming.value.filter((x) => x.id !== c.id)
}
async function withdraw(c: Connection) {
  await network.remove(c.id)
  outgoing.value = outgoing.value.filter((x) => x.id !== c.id)
}
async function disconnect(c: Connection) {
  await network.remove(c.id)
  connections.value = connections.value.filter((x) => x.id !== c.id)
}
async function connect(s: Suggestion) {
  await network.connect(s.username)
  asked.value = new Set([...asked.value, s.username])
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Network</h1>
  <p class="mt-1 text-muted">The people you learn and teach with.</p>

  <div class="mt-8 grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
    <div class="grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-8">
      <section v-if="incoming.length" aria-labelledby="requests-title">
        <h2 id="requests-title" class="mb-3 text-lg font-semibold">
          Requests <span class="font-mono text-sm font-normal text-muted">{{ incoming.length }}</span>
        </h2>
        <Card class="divide-y divide-line">
          <PersonCard v-for="c in incoming" :key="c.id" :person="c.person" class="p-4">
            <Button size="sm" @click="accept(c)">Accept</Button>
            <Button size="sm" variant="ghost" @click="decline(c)">Ignore</Button>
          </PersonCard>
        </Card>
      </section>

      <section aria-label="Your network">
        <div class="mb-3 flex gap-1 border-b border-line" role="tablist">
          <button
            v-for="t in tabs"
            :key="t.id"
            type="button"
            role="tab"
            :aria-selected="tab === t.id"
            class="-mb-px h-10 cursor-pointer border-b-2 px-3 text-sm transition-colors duration-quick"
            :class="tab === t.id ? 'border-accent text-ink' : 'border-transparent text-muted hover:text-ink'"
            @click="tab = t.id"
          >
            {{ t.label }} <span class="font-mono text-xs text-muted">{{ t.count }}</span>
          </button>
        </div>
        <div role="tabpanel">
          <template v-if="tab === 'connections'">
            <Card v-if="connections.length" class="divide-y divide-line">
              <PersonCard v-for="c in connections" :key="c.id" :person="c.person" class="p-4">
                <Button size="sm" variant="ghost" @click="disconnect(c)">Remove</Button>
              </PersonCard>
            </Card>
            <p v-else-if="loaded" class="py-10 text-center text-muted">
              <PhUsersThree :size="28" weight="light" class="mx-auto mb-2" />
              No connections yet. Start with the suggestions.
            </p>
          </template>
          <template v-else>
            <Card v-if="(tab === 'followers' ? followers : following).length" class="divide-y divide-line">
              <PersonCard
                v-for="f in tab === 'followers' ? followers : following"
                :key="f.person.id"
                :person="f.person"
                class="p-4"
              />
            </Card>
            <p v-else-if="loaded" class="py-10 text-center text-muted">
              {{ tab === 'followers' ? 'No followers yet.' : 'You are not following anyone yet.' }}
            </p>
          </template>
        </div>
      </section>

      <section v-if="outgoing.length" aria-labelledby="sent-title">
        <h2 id="sent-title" class="mb-3 text-sm font-medium text-muted">Sent requests</h2>
        <Card class="divide-y divide-line">
          <PersonCard v-for="c in outgoing" :key="c.id" :person="c.person" class="p-4">
            <Button size="sm" variant="ghost" @click="withdraw(c)">Withdraw</Button>
          </PersonCard>
        </Card>
      </section>
    </div>

    <aside aria-labelledby="suggest-title" class="min-w-0">
      <h2 id="suggest-title" class="mb-3 text-lg font-semibold">People you may know</h2>
      <Card v-if="suggestions.length" class="divide-y divide-line">
        <PersonCard
          v-for="s in suggestions"
          :key="s.id"
          :person="s"
          :note="`${s.shared_skills} shared skill${s.shared_skills === 1 ? '' : 's'}`"
          class="p-4"
        >
          <Button v-if="!asked.has(s.username)" size="sm" variant="secondary" @click="connect(s)">
            Connect
          </Button>
          <span v-else class="font-mono text-xs text-muted">sent</span>
        </PersonCard>
      </Card>
      <p v-else-if="loaded" class="text-sm text-muted">
        Add skills to your profile and we will suggest people who share them.
      </p>
    </aside>
  </div>
</template>
