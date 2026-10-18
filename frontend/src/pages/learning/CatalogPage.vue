<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import { learning, type CourseSummary, type Level } from '@/api/learning'
import CourseCard from '@/features/learning/CourseCard.vue'
import Button from '@/components/ui/Button.vue'

const search = ref('')
const level = ref<Level | ''>('')
const courses = ref<CourseSummary[]>([])
const next = ref<string | null>(null)
const loading = ref(true)

async function load(reset = true) {
  loading.value = true
  const cursor = reset
    ? undefined
    : (new URL(next.value!, location.origin).searchParams.get('cursor') ?? undefined)
  const page = await learning.courses({
    search: search.value,
    level: level.value,
    status: 'published',
    cursor,
  })
  courses.value = reset ? page.results : [...courses.value, ...page.results]
  next.value = page.next
  loading.value = false
}

let timer: ReturnType<typeof setTimeout>
watch(
  [search, level],
  () => {
    clearTimeout(timer)
    timer = setTimeout(() => load(), 250)
  },
  { immediate: true },
)
</script>

<template>
  <h1 class="text-3xl font-semibold">Courses</h1>
  <p class="mt-1 text-muted">Everything published on the platform.</p>

  <div class="mt-6 flex flex-wrap gap-3">
    <label class="relative min-w-0 flex-1 basis-64">
      <span class="sr-only">Search courses</span>
      <PhMagnifyingGlass
        :size="18"
        weight="light"
        class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted"
      />
      <input
        v-model="search"
        type="search"
        placeholder="Search by title or summary"
        class="h-11 w-full rounded-md bg-surface pr-3 pl-10 text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
      />
    </label>
    <label>
      <span class="sr-only">Level</span>
      <select
        v-model="level"
        class="h-11 rounded-md bg-surface px-3 text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
      >
        <option value="">All levels</option>
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </select>
    </label>
  </div>

  <ul v-if="courses.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <li v-for="course in courses" :key="course.id"><CourseCard :course="course" /></li>
  </ul>
  <p v-else-if="!loading" class="mt-10 text-center text-muted">No courses match. Try another search.</p>
  <div v-if="next" class="mt-6 flex justify-center">
    <Button variant="secondary" :loading="loading" @click="load(false)">Load more</Button>
  </div>
</template>
