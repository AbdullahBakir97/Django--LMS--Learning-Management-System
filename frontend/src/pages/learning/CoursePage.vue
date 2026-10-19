<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  PhCheckCircle,
  PhCircle,
  PhLockSimple,
  PhEye,
  PhPencilSimple,
  PhSealCheck,
} from '@phosphor-icons/vue'
import { learning, price, type Course, type Progress } from '@/api/learning'
import { ApiError } from '@/api/client'
import { useSessionStore } from '@/stores/session'
import { renderMarkdown } from '@/features/learning/markdown'
import ProgressBar from '@/features/learning/ProgressBar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Alert from '@/components/ui/Alert.vue'
import Tag from '@/components/ui/Tag.vue'

const props = defineProps<{ slug: string }>()
const session = useSessionStore()
const router = useRouter()
const route = useRoute()
const course = ref<Course | null>(null)
const progress = ref<Progress | null>(null)
const error = ref('')
const enrolling = ref(false)

const isOwner = computed(() => course.value?.instructor.id === session.user?.id)
const done = computed(() => new Set(progress.value?.completed_lessons ?? []))
const nextLesson = computed(
  () => course.value?.lessons.find((l) => !done.value.has(l.id)) ?? course.value?.lessons[0],
)

async function load() {
  error.value = ''
  try {
    course.value = await learning.course(props.slug)
    progress.value = (await learning.progress(props.slug)) ?? null
  } catch (e) {
    error.value =
      e instanceof ApiError && e.problem.status === 404
        ? 'This course does not exist.'
        : 'Could not load the course.'
  }
}
watch(() => props.slug, load, { immediate: true })

// Back from the payment page: the webhook usually lands within seconds, so check a few times.
const confirming = ref(route.query.paid === '1')
let poll: ReturnType<typeof setTimeout> | undefined
async function waitForPayment(tries = 15) {
  if (!confirming.value) return
  if (progress.value || tries === 0) {
    confirming.value = false
    router.replace({ query: {} })
    return
  }
  poll = setTimeout(async () => {
    progress.value = (await learning.progress(props.slug).catch(() => undefined)) ?? null
    waitForPayment(tries - 1)
  }, 2000)
}
watch(course, (c) => c && waitForPayment(), { once: true })
onBeforeUnmount(() => clearTimeout(poll))

async function buy() {
  enrolling.value = true
  error.value = ''
  try {
    window.location.assign((await learning.checkout(props.slug)).url)
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not start the payment.') : ''
    enrolling.value = false
  }
}

async function enroll() {
  enrolling.value = true
  error.value = ''
  try {
    progress.value = await learning.enroll(props.slug)
    if (nextLesson.value)
      router.push({ name: 'lesson', params: { slug: props.slug, id: nextLesson.value.id } })
  } catch (e) {
    if (e instanceof ApiError) {
      const errs = e.problem.errors
      const pre = Array.isArray(errs) ? undefined : errs?.prerequisites
      error.value = Array.isArray(pre) ? pre.join(' ') : (e.nonField ?? 'Could not enrol.')
    }
  } finally {
    enrolling.value = false
  }
}
</script>

<template>
  <Alert v-if="error && !course" tone="danger">{{ error }}</Alert>
  <template v-if="course">
    <div class="flex flex-wrap items-center gap-2">
      <Tag>{{ course.level }}</Tag>
      <Tag v-if="course.status === 'draft'">draft</Tag>
    </div>
    <h1 class="mt-3 text-4xl font-semibold">{{ course.title }}</h1>
    <p v-if="course.summary" class="mt-2 max-w-prose text-lg text-muted">{{ course.summary }}</p>
    <p class="mt-3 text-sm text-muted">
      Taught by
      <RouterLink
        class="text-ink hover:text-accent"
        :to="{ name: 'profile', params: { username: course.instructor.username } }"
      >
        {{
          `${course.instructor.first_name} ${course.instructor.last_name}`.trim() ||
          course.instructor.username
        }}
      </RouterLink>
      · {{ course.lesson_count }} lessons · {{ course.enrollment_count }} enrolled
    </p>

    <div class="mt-8 grid gap-6 lg:grid-cols-[1fr_20rem]">
      <div class="grid content-start gap-6">
        <div
          v-if="course.description"
          class="prose-lms max-w-prose"
          v-html="renderMarkdown(course.description)"
        />
        <Card class="p-5">
          <h2 class="text-lg font-semibold">Lessons</h2>
          <ol class="mt-3 divide-y divide-line">
            <li v-for="lesson in course.lessons" :key="lesson.id">
              <RouterLink
                v-if="progress || lesson.is_free_preview || isOwner"
                :to="{ name: 'lesson', params: { slug: course.slug, id: lesson.id } }"
                class="flex items-center gap-3 py-3 hover:text-accent"
              >
                <PhCheckCircle
                  v-if="done.has(lesson.id)"
                  :size="20"
                  weight="fill"
                  class="shrink-0 text-accent"
                />
                <PhEye
                  v-else-if="!progress && lesson.is_free_preview"
                  :size="20"
                  weight="light"
                  class="shrink-0 text-muted"
                />
                <PhCircle v-else :size="20" weight="light" class="shrink-0 text-muted" />
                <span class="font-mono text-xs text-muted">{{ String(lesson.order).padStart(2, '0') }}</span>
                <span class="min-w-0 flex-1 truncate">{{ lesson.title }}</span>
                <Tag v-if="lesson.has_quiz">quiz</Tag>
              </RouterLink>
              <span v-else class="flex items-center gap-3 py-3 text-muted">
                <PhLockSimple :size="20" weight="light" class="shrink-0" />
                <span class="font-mono text-xs">{{ String(lesson.order).padStart(2, '0') }}</span>
                <span class="min-w-0 flex-1 truncate">{{ lesson.title }}</span>
              </span>
            </li>
          </ol>
          <p v-if="!course.lessons.length" class="mt-2 text-sm text-muted">No lessons yet.</p>
        </Card>
      </div>

      <Card class="grid h-fit gap-4 p-5 lg:sticky lg:top-20">
        <template v-if="isOwner">
          <p class="text-sm text-muted">You teach this course.</p>
          <RouterLink :to="{ name: 'course-editor', params: { slug: course.slug } }">
            <Button variant="secondary" class="w-full"
              ><PhPencilSimple :size="16" weight="light" /> Edit course</Button
            >
          </RouterLink>
        </template>
        <template v-else-if="progress">
          <ProgressBar :done="progress.completed_lessons.length" :total="course.lessons.length" />
          <template v-if="progress.status === 'completed'">
            <Alert tone="success">Completed. Well done.</Alert>
            <RouterLink
              v-if="progress.certificate_code"
              :to="{ name: 'certificate', params: { code: progress.certificate_code } }"
            >
              <Button class="w-full"><PhSealCheck :size="18" weight="light" /> View certificate</Button>
            </RouterLink>
          </template>
          <RouterLink
            v-else-if="nextLesson"
            :to="{ name: 'lesson', params: { slug: course.slug, id: nextLesson.id } }"
          >
            <Button class="w-full">Continue</Button>
          </RouterLink>
        </template>
        <template v-else-if="confirming">
          <Alert tone="success">Payment received. Unlocking your course…</Alert>
        </template>
        <template v-else>
          <Alert v-if="error" tone="danger">{{ error }}</Alert>
          <template v-if="course.price_cents">
            <p class="font-mono text-2xl">{{ price(course) }}</p>
            <Button :loading="enrolling" :disabled="course.status !== 'published'" @click="buy"
              >Buy course</Button
            >
            <p class="text-xs text-muted">
              Secure card payment. Lifetime access once paid. Free preview lessons are open to all.
            </p>
          </template>
          <Button v-else :loading="enrolling" :disabled="course.status !== 'published'" @click="enroll"
            >Enrol for free</Button
          >
          <p class="text-xs text-muted">
            Finish every lesson and pass every quiz to earn a verifiable certificate.
          </p>
        </template>
      </Card>
    </div>
  </template>
</template>
