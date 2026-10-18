<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhPlus } from '@phosphor-icons/vue'
import { learning, type CourseSummary } from '@/api/learning'
import { useSessionStore } from '@/stores/session'
import CourseCard from '@/features/learning/CourseCard.vue'
import Button from '@/components/ui/Button.vue'

const session = useSessionStore()
const courses = ref<CourseSummary[] | null>(null)

onMounted(async () => {
  const page = await learning.courses({ instructor: String(session.user!.id) })
  courses.value = page.results
})
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Teaching</h1>
      <p class="mt-1 text-muted">Courses you author, drafts included.</p>
    </div>
    <RouterLink :to="{ name: 'course-new' }"
      ><Button><PhPlus :size="18" weight="light" /> New course</Button></RouterLink
    >
  </div>
  <p v-if="courses && !courses.length" class="mt-10 text-muted">You have not created a course yet.</p>
  <ul v-else class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <li v-for="c in courses ?? []" :key="c.id"><CourseCard :course="c" /></li>
  </ul>
</template>
