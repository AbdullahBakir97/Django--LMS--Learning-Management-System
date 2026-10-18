<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { PhBriefcase, PhMagnifyingGlass } from '@phosphor-icons/vue'
import { careers, labels, type Job, type JobFilters } from '@/api/careers'
import { cursorOf } from '@/api/community'
import Button from '@/components/ui/Button.vue'
import JobCard from '@/features/careers/JobCard.vue'

const filters = reactive<JobFilters>({
  search: '',
  workplace: '',
  employment_type: '',
  level: '',
  sort: 'newest',
  saved: false,
})
const jobs = ref<Job[]>([])
const next = ref<string | null>(null)
const loaded = ref(false)
const select =
  'h-10 rounded-md bg-surface px-2 text-sm text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none'

async function load(more = false) {
  const page = await careers.jobs({ ...filters, cursor: more ? cursorOf(next.value) : undefined })
  jobs.value = more ? [...jobs.value, ...page.results] : page.results
  next.value = page.next
  loaded.value = true
}
let timer: ReturnType<typeof setTimeout> | undefined
watch(
  filters,
  () => {
    clearTimeout(timer)
    timer = setTimeout(() => load(), 200)
  },
  { deep: true, immediate: true },
)
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Jobs</h1>
      <p class="mt-1 text-muted">Roles that fit what you are learning.</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <RouterLink :to="{ name: 'applications' }"
        ><Button variant="secondary">Your applications</Button></RouterLink
      >
      <RouterLink :to="{ name: 'companies' }"><Button variant="ghost">Companies</Button></RouterLink>
    </div>
  </div>

  <div class="mt-6 grid gap-3 rounded-lg bg-surface p-3 ring-1 ring-line sm:grid-cols-[minmax(0,1fr)_auto]">
    <label class="relative">
      <span class="sr-only">Search jobs</span>
      <PhMagnifyingGlass
        :size="18"
        weight="light"
        class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted"
      />
      <input
        v-model="filters.search"
        type="search"
        placeholder="Title, company, place"
        class="h-10 w-full rounded-md bg-page pr-3 pl-9 text-sm ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
      />
    </label>
    <div class="flex flex-wrap items-center gap-2">
      <select v-model="filters.workplace" :class="select" aria-label="Workplace">
        <option value="">Any workplace</option>
        <option v-for="(l, v) in labels.workplace" :key="v" :value="v">{{ l }}</option>
      </select>
      <select v-model="filters.employment_type" :class="select" aria-label="Type">
        <option value="">Any type</option>
        <option v-for="(l, v) in labels.type" :key="v" :value="v">{{ l }}</option>
      </select>
      <select v-model="filters.level" :class="select" aria-label="Level">
        <option value="">Any level</option>
        <option v-for="(l, v) in labels.level" :key="v" :value="v">{{ l }}</option>
      </select>
      <select v-model="filters.sort" :class="select" aria-label="Sort">
        <option value="newest">Newest</option>
        <option value="match">Best skill match</option>
      </select>
      <label class="inline-flex h-10 cursor-pointer items-center gap-2 px-1 text-sm">
        <input v-model="filters.saved" type="checkbox" class="size-4 accent-[var(--c-accent)]" /> Saved
      </label>
    </div>
  </div>

  <div class="mt-6 grid max-w-3xl gap-3">
    <JobCard v-for="(j, i) in jobs" :key="j.id" :job="j" @update="jobs[i] = $event" />
    <div v-if="loaded && !jobs.length" class="grid justify-items-center gap-2 py-12 text-center text-muted">
      <PhBriefcase :size="28" weight="light" />
      {{ filters.saved ? 'No saved jobs yet.' : 'No jobs match these filters.' }}
    </div>
    <div v-if="next" class="flex justify-center">
      <Button variant="ghost" @click="load(true)">Show more</Button>
    </div>
  </div>
</template>
