<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { learning, type Course, type CourseAnalytics } from '@/api/learning'
import Alert from '@/components/ui/Alert.vue'
import Avatar from '@/components/ui/Avatar.vue'
import Card from '@/components/ui/Card.vue'
import LessonDropoff from '@/features/analytics/LessonDropoff.vue'
import WeeklyBars from '@/features/analytics/WeeklyBars.vue'
import { timeAgo } from '@/features/notifications/format'

const props = defineProps<{ slug: string }>()
const course = ref<Course | null>(null)
const data = ref<CourseAnalytics | null>(null)
const error = ref('')

watch(
  () => props.slug,
  async (slug) => {
    error.value = ''
    try {
      ;[course.value, data.value] = await Promise.all([learning.course(slug), learning.analytics(slug)])
    } catch {
      error.value = 'Analytics are only for the course’s instructor.'
    }
  },
  { immediate: true },
)
</script>

<template>
  <p class="font-mono text-xs text-muted">
    <RouterLink :to="{ name: 'teach' }" class="hover:text-ink">Teaching</RouterLink> /
    <RouterLink v-if="course" :to="{ name: 'course-editor', params: { slug } }" class="hover:text-ink">{{
      course.title
    }}</RouterLink>
  </p>
  <h1 class="mt-1 text-3xl font-semibold">Analytics</h1>
  <Alert v-if="error" tone="danger" class="mt-6">{{ error }}</Alert>

  <template v-else-if="data">
    <dl class="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Enrolled</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">{{ data.enrolled }}</dd>
        <dd class="text-xs text-muted">{{ data.active }} still learning</dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Completed</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">{{ data.completion_rate }}%</dd>
        <dd class="text-xs text-muted">{{ data.completed }} of {{ data.enrolled }}</dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Time to finish</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">
          {{ data.average_days_to_complete ?? '—' }}
        </dd>
        <dd class="text-xs text-muted">average days</dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Stalled</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">{{ data.stalled_count }}</dd>
        <dd class="text-xs text-muted">no progress in 14 days</dd>
      </Card>
    </dl>

    <div
      class="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]"
    >
      <Card class="grid content-start gap-3 p-5">
        <h2 class="font-semibold">Enrolments per week</h2>
        <WeeklyBars :weeks="data.weekly_enrolments" />
      </Card>
      <Card class="grid content-start gap-4 p-5">
        <div>
          <h2 class="font-semibold">Where learners stop</h2>
          <p class="text-sm text-muted">Share of everyone enrolled who finished each lesson.</p>
        </div>
        <LessonDropoff v-if="data.lessons.length" :lessons="data.lessons" :enrolled="data.enrolled" />
        <p v-else class="text-sm text-muted">Add lessons to see how far learners get.</p>
      </Card>
    </div>

    <div class="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-2">
      <Card class="grid content-start gap-3 p-5">
        <h2 class="font-semibold">Quizzes</h2>
        <p v-if="!data.quizzes.length" class="text-sm text-muted">No quiz attempts yet.</p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left font-mono text-xs text-muted uppercase">
                <th class="py-2 pr-3 font-normal">Quiz</th>
                <th class="py-2 pr-3 text-right font-normal">Passed</th>
                <th class="py-2 pr-3 text-right font-normal">Avg score</th>
                <th class="py-2 text-right font-normal">Attempts</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="q in data.quizzes" :key="q.lesson_id">
                <td class="py-2 pr-3">{{ q.title }}</td>
                <td class="py-2 pr-3 text-right tabular-nums">{{ q.passed }} / {{ q.learners }}</td>
                <td class="py-2 pr-3 text-right tabular-nums">{{ q.average_score }}%</td>
                <td class="py-2 text-right tabular-nums">
                  {{ (q.attempts / Math.max(1, q.learners)).toFixed(1) }} each
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
      <Card class="grid content-start gap-3 p-5">
        <div>
          <h2 class="font-semibold">Stalled learners</h2>
          <p class="text-sm text-muted">Longest without progress first. A message can help.</p>
        </div>
        <p v-if="!data.stalled.length" class="text-sm text-muted">Everyone is moving.</p>
        <ul v-else class="grid gap-3">
          <li v-for="s in data.stalled" :key="s.username" class="flex items-center gap-3">
            <Avatar :name="s.name" size="sm" />
            <div class="min-w-0 flex-1">
              <RouterLink
                :to="{ name: 'profile', params: { username: s.username } }"
                class="block truncate text-sm font-medium hover:underline"
                >{{ s.name }}</RouterLink
              >
              <span class="font-mono text-xs text-muted"
                >{{ s.lessons_done }} of {{ data.lesson_count }} lessons · active
                {{ timeAgo(s.last_active) }}</span
              >
            </div>
          </li>
        </ul>
        <p v-if="data.stalled_count > data.stalled.length" class="text-xs text-muted">
          And {{ data.stalled_count - data.stalled.length }} more.
        </p>
      </Card>
    </div>
  </template>
</template>
