<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhBooks,
  PhBriefcase,
  PhBuildings,
  PhCalendarBlank,
  PhMagnifyingGlass,
  PhUser,
  PhUsersFour,
} from '@phosphor-icons/vue'
import { search, SEARCH_KINDS, type Hit, type SearchKind, type SearchResults } from '@/api/search'
import Avatar from '@/components/ui/Avatar.vue'

const open = defineModel<boolean>('open', { default: false })
const router = useRouter()
const el = ref<HTMLDialogElement>()
const input = ref<HTMLInputElement>()
const q = ref('')
const kind = ref<SearchKind | null>(null)
const results = ref<SearchResults>({})
const active = ref(0)
const loading = ref(false)

const label: Record<SearchKind, string> = {
  people: 'People',
  courses: 'Courses',
  groups: 'Groups',
  events: 'Events',
  jobs: 'Jobs',
  companies: 'Companies',
}
const icon = {
  people: PhUser,
  courses: PhBooks,
  groups: PhUsersFour,
  events: PhCalendarBlank,
  jobs: PhBriefcase,
  companies: PhBuildings,
}

const groups = computed(() =>
  SEARCH_KINDS.filter((k) => results.value[k]?.length).map((k) => ({ kind: k, hits: results.value[k]! })),
)
const flat = computed(() => groups.value.flatMap((g) => g.hits))

watch(open, async (v) => {
  if (v) {
    el.value?.showModal()
    await nextTick()
    input.value?.select()
  } else el.value?.close()
})

// Only the newest answer is shown, however the requests race.
let latest = 0
let timer: ReturnType<typeof setTimeout> | undefined
watch([q, kind], () => {
  clearTimeout(timer)
  if (!q.value.trim()) {
    results.value = {}
    return
  }
  timer = setTimeout(async () => {
    const mine = ++latest
    loading.value = true
    try {
      const found = await search(q.value, kind.value ?? undefined)
      if (mine === latest) {
        results.value = found
        active.value = 0
      }
    } finally {
      if (mine === latest) loading.value = false
    }
  }, 180)
})

function go(hit: Hit | undefined) {
  if (!hit) return
  open.value = false
  router.push(hit.url)
}

function move(step: number) {
  if (!flat.value.length) return
  active.value = (active.value + step + flat.value.length) % flat.value.length
  document.getElementById(`hit-${active.value}`)?.scrollIntoView({ block: 'nearest' })
}

const indexOf = (hit: Hit) => flat.value.indexOf(hit)
</script>

<template>
  <dialog
    ref="el"
    class="mx-auto mt-[10vh] w-[min(94vw,40rem)] overflow-hidden rounded-lg bg-surface p-0 text-ink shadow-pop ring-1 ring-line backdrop:bg-ink/40 backdrop:backdrop-blur-[2px]"
    aria-label="Search"
    @close="open = false"
    @click.self="open = false"
  >
    <div class="flex items-center gap-3 border-b border-line px-4">
      <PhMagnifyingGlass :size="20" weight="light" class="shrink-0 text-muted" aria-hidden="true" />
      <input
        id="search-input"
        ref="input"
        v-model="q"
        type="text"
        enterkeyhint="search"
        role="combobox"
        aria-label="Search everything"
        aria-autocomplete="list"
        aria-controls="search-results"
        :aria-expanded="flat.length > 0"
        :aria-activedescendant="flat.length ? `hit-${active}` : undefined"
        placeholder="Search people, courses, groups, events, jobs…"
        class="h-14 min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-muted"
        autocomplete="off"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="go(flat[active])"
      />
      <kbd class="hidden rounded-sm bg-surface-2 px-1.5 py-0.5 font-mono text-xs text-muted sm:block"
        >Esc</kbd
      >
    </div>
    <div
      class="flex gap-1 overflow-x-auto border-b border-line px-3 py-2"
      role="group"
      aria-label="Only show"
    >
      <button
        v-for="k in [null, ...SEARCH_KINDS]"
        :key="k ?? 'all'"
        type="button"
        class="h-7 shrink-0 cursor-pointer rounded-sm px-2.5 text-sm transition-colors duration-quick"
        :class="kind === k ? 'bg-accent-soft text-accent' : 'text-muted hover:bg-surface-2 hover:text-ink'"
        :aria-pressed="kind === k"
        @click="kind = k"
      >
        {{ k ? label[k] : 'All' }}
      </button>
    </div>
    <div id="search-results" role="listbox" aria-label="Results" class="max-h-[60vh] overflow-y-auto py-2">
      <p v-if="!q.trim()" class="px-4 py-8 text-center text-sm text-muted">
        Start typing. Results appear as you go.
      </p>
      <p v-else-if="!loading && !flat.length" class="px-4 py-8 text-center text-sm text-muted">
        Nothing matches “{{ q }}”.
      </p>
      <section v-for="g in groups" :key="g.kind" :aria-label="label[g.kind]">
        <h3 class="px-4 pt-2 pb-1 font-mono text-xs tracking-wider text-muted uppercase">
          {{ label[g.kind] }}
        </h3>
        <div
          v-for="hit in g.hits"
          :id="`hit-${indexOf(hit)}`"
          :key="`${hit.kind}-${hit.id}`"
          role="option"
          :aria-selected="indexOf(hit) === active"
          class="mx-2 flex cursor-pointer items-center gap-3 rounded-md px-2 py-2"
          :class="indexOf(hit) === active ? 'bg-surface-2' : ''"
          @mousemove="active = indexOf(hit)"
          @click="go(hit)"
        >
          <Avatar v-if="hit.kind === 'people'" :name="hit.title" :src="hit.image" size="sm" />
          <img v-else-if="hit.image" :src="hit.image" alt="" class="size-8 rounded-md object-cover" />
          <span v-else class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-2 text-muted">
            <component :is="icon[hit.kind]" :size="18" weight="light" />
          </span>
          <span class="min-w-0">
            <span class="block truncate text-sm font-medium">{{ hit.title }}</span>
            <span class="block truncate text-xs text-muted">{{ hit.subtitle }}</span>
          </span>
        </div>
      </section>
    </div>
  </dialog>
</template>
