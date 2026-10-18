<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhLockSimple, PhMagnifyingGlass, PhPlus, PhUsersThree } from '@phosphor-icons/vue'
import { community, cursorOf, type Group } from '@/api/community'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tag from '@/components/ui/Tag.vue'
import GroupForm from '@/features/community/GroupForm.vue'

const router = useRouter()
const mine = ref<Group[]>([])
const all = ref<Group[]>([])
const next = ref<string | null>(null)
const search = ref('')
const creating = ref(false)

async function loadAll(more = false) {
  const page = await community.groups({
    search: search.value || undefined,
    cursor: more ? cursorOf(next.value) : undefined,
  })
  all.value = more ? [...all.value, ...page.results] : page.results
  next.value = page.next
}
onMounted(async () => {
  mine.value = (await community.groups({ mine: true })).results
  await loadAll()
})
let timer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(timer)
  timer = setTimeout(() => loadAll(), 250)
})

function created(g: Group) {
  creating.value = false
  router.push({ name: 'group', params: { slug: g.slug } })
}
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Groups</h1>
      <p class="mt-1 text-muted">Study circles, cohorts and communities of practice.</p>
    </div>
    <Button @click="creating = true"><PhPlus :size="18" weight="light" /> New group</Button>
  </div>

  <section v-if="mine.length" class="mt-8" aria-labelledby="mine-title">
    <h2 id="mine-title" class="mb-3 text-lg font-semibold">Yours</h2>
    <div class="flex flex-wrap gap-2">
      <RouterLink
        v-for="g in mine"
        :key="g.slug"
        :to="{ name: 'group', params: { slug: g.slug } }"
        class="inline-flex h-9 items-center gap-2 rounded-full bg-surface px-3 text-sm ring-1 ring-line hover:ring-line-strong"
      >
        <component
          :is="g.privacy === 'private' ? PhLockSimple : PhUsersThree"
          :size="16"
          weight="light"
          class="text-muted"
        />
        {{ g.name }}
        <Tag v-if="g.my_status === 'pending'">pending</Tag>
      </RouterLink>
    </div>
  </section>

  <section class="mt-10" aria-labelledby="all-title">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <h2 id="all-title" class="text-lg font-semibold">Discover</h2>
      <label class="relative w-full sm:w-72">
        <span class="sr-only">Search groups</span>
        <PhMagnifyingGlass
          :size="18"
          weight="light"
          class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted"
        />
        <input
          v-model="search"
          type="search"
          placeholder="Search groups"
          class="h-10 w-full rounded-md bg-surface pr-3 pl-9 text-sm ring-1 ring-line-strong placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
        />
      </label>
    </div>
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink
        v-for="g in all"
        :key="g.slug"
        :to="{ name: 'group', params: { slug: g.slug } }"
        class="min-w-0"
      >
        <Card class="flex h-full flex-col p-5 transition-shadow duration-base hover:shadow-pop">
          <div class="flex items-center gap-2 text-sm text-muted">
            <component
              :is="g.privacy === 'private' ? PhLockSimple : PhUsersThree"
              :size="16"
              weight="light"
            />
            {{ g.privacy === 'private' ? 'Private' : 'Public' }} · {{ g.member_count }} member{{
              g.member_count === 1 ? '' : 's'
            }}
          </div>
          <h3 class="mt-2 font-semibold text-ink">{{ g.name }}</h3>
          <p class="mt-1 line-clamp-3 text-sm text-muted">{{ g.description || 'No description yet.' }}</p>
          <p v-if="g.my_status" class="mt-auto pt-3 font-mono text-xs text-accent">
            {{
              g.my_status === 'active' ? (g.my_role === 'member' ? 'member' : g.my_role) : 'request pending'
            }}
          </p>
        </Card>
      </RouterLink>
    </div>
    <p v-if="!all.length" class="py-10 text-center text-muted">No groups match.</p>
    <div v-if="next" class="mt-6 flex justify-center">
      <Button variant="ghost" @click="loadAll(true)">Show more</Button>
    </div>
  </section>

  <Dialog v-model:open="creating" title="New group">
    <GroupForm v-if="creating" @saved="created" />
  </Dialog>
</template>
