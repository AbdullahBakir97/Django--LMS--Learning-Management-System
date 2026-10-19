<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhArrowLeft, PhCheck, PhCheckCircle, PhCircle, PhPaperclip } from '@phosphor-icons/vue'
import { learning, type Course, type Lesson, type Progress, type Quiz } from '@/api/learning'
import { ApiError, apiBlob } from '@/api/client'
import { renderMarkdown } from '@/features/learning/markdown'
import QuizRunner from '@/features/learning/QuizRunner.vue'
import ProgressBar from '@/features/learning/ProgressBar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Alert from '@/components/ui/Alert.vue'
import DiscussionThread from '@/features/engagement/DiscussionThread.vue'

const props = defineProps<{ slug: string; id: string }>()
const router = useRouter()
const course = ref<Course | null>(null)
const lesson = ref<Lesson | null>(null)
const quiz = ref<Quiz | null>(null)
const progress = ref<Progress | null>(null)
const error = ref('')
const busy = ref(false)

const lessonId = computed(() => Number(props.id))
const done = computed(() => new Set(progress.value?.completed_lessons ?? []))
const index = computed(() => course.value?.lessons.findIndex((l) => l.id === lessonId.value) ?? -1)
const next = computed(() => course.value?.lessons[index.value + 1])
const embed = computed(() => {
  const url = lesson.value?.video_url ?? ''
  const yt = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})/)
  if (yt) return { kind: 'iframe', src: `https://www.youtube-nocookie.com/embed/${yt[1]}` }
  if (/\.(mp4|webm)(\?|$)/i.test(url)) return { kind: 'video', src: url }
  return url ? { kind: 'link', src: url } : null
})

async function load() {
  error.value = ''
  quiz.value = null
  try {
    course.value ??= await learning.course(props.slug)
    progress.value = (await learning.progress(props.slug)) ?? null
    lesson.value = await learning.lesson(props.slug, lessonId.value)
    if (lesson.value.has_quiz) quiz.value = await learning.quiz(lessonId.value)
  } catch (e) {
    error.value =
      e instanceof ApiError ? (e.problem.detail ?? 'Could not open this lesson.') : 'Network error.'
  }
}
watch(() => props.id, load, { immediate: true })

async function complete() {
  busy.value = true
  progress.value = await learning.completeLesson(props.slug, lessonId.value)
  busy.value = false
  if (next.value) router.push({ name: 'lesson', params: { slug: props.slug, id: next.value.id } })
}

async function refreshProgress() {
  progress.value = (await learning.progress(props.slug)) ?? null
}

// Files sit behind the API's permission check, so they are fetched with the token.
async function download(a: Lesson['attachments'][number]) {
  const url = URL.createObjectURL(await apiBlob(a.url))
  const link = Object.assign(document.createElement('a'), { href: url, download: a.title })
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
</script>

<template>
  <RouterLink
    :to="{ name: 'course', params: { slug } }"
    class="inline-flex items-center gap-1 text-sm text-muted hover:text-ink"
  >
    <PhArrowLeft :size="16" weight="light" /> {{ course?.title ?? 'Course' }}
  </RouterLink>

  <div class="mt-4 grid gap-6 lg:grid-cols-[1fr_17rem]">
    <div class="min-w-0">
      <Alert v-if="error" tone="danger">{{ error }}</Alert>
      <template v-if="lesson && !error">
        <p class="font-mono text-xs text-muted">Lesson {{ lesson.order }}</p>
        <h1 class="mt-1 text-3xl font-semibold">{{ lesson.title }}</h1>

        <div v-if="embed" class="mt-6">
          <div
            v-if="embed.kind === 'iframe'"
            class="aspect-video overflow-hidden rounded-lg ring-1 ring-line"
          >
            <iframe
              :src="embed.src"
              class="size-full"
              title="Lesson video"
              allow="encrypted-media; picture-in-picture"
              allowfullscreen
            />
          </div>
          <video
            v-else-if="embed.kind === 'video'"
            :src="embed.src"
            controls
            class="w-full rounded-lg ring-1 ring-line"
          />
          <a v-else :href="embed.src" target="_blank" rel="noopener" class="text-accent hover:underline"
            >Watch the video</a
          >
        </div>

        <article class="prose-lms mt-6 max-w-prose" v-html="renderMarkdown(lesson.content)" />

        <ul v-if="lesson.attachments.length" class="mt-6 grid gap-2">
          <li v-for="a in lesson.attachments" :key="a.id">
            <button
              type="button"
              class="inline-flex cursor-pointer items-center gap-2 text-sm text-accent hover:underline"
              @click="download(a)"
            >
              <PhPaperclip :size="16" weight="light" />{{ a.title }}
            </button>
          </li>
        </ul>

        <Card v-if="quiz && progress" class="mt-8 p-5">
          <QuizRunner :lesson-id="lesson.id" :quiz="quiz" @passed="refreshProgress" />
        </Card>

        <div v-if="progress" class="mt-8 flex flex-wrap items-center gap-3">
          <Button v-if="!lesson.has_quiz && !done.has(lesson.id)" :loading="busy" @click="complete">
            <PhCheck :size="18" weight="light" /> Mark complete{{ next ? ' and continue' : '' }}
          </Button>
          <RouterLink v-else-if="next" :to="{ name: 'lesson', params: { slug, id: next.id } }">
            <Button>Next lesson</Button>
          </RouterLink>
          <RouterLink v-else :to="{ name: 'course', params: { slug } }"
            ><Button variant="secondary">Back to course</Button></RouterLink
          >
        </div>
        <Alert v-else class="mt-8"
          >This is a free preview. Enrol in the course to track progress and take quizzes.</Alert
        >

        <DiscussionThread
          class="mt-12 border-t border-line pt-8"
          :target="{ key: 'lesson', id: lesson.id }"
          :title="lesson.title"
        />
      </template>
    </div>

    <aside v-if="course" class="h-fit min-w-0 lg:sticky lg:top-20">
      <Card class="p-4">
        <ProgressBar
          v-if="progress"
          :done="progress.completed_lessons.length"
          :total="course.lessons.length"
          class="mb-4"
        />
        <ol class="grid grid-cols-[minmax(0,1fr)] gap-0.5">
          <li v-for="l in course.lessons" :key="l.id">
            <RouterLink
              :to="{ name: 'lesson', params: { slug, id: l.id } }"
              class="flex items-center gap-2 rounded-md px-2 py-2 text-sm hover:bg-surface-2"
              :class="l.id === lessonId ? 'bg-accent-soft text-accent' : 'text-ink'"
            >
              <PhCheckCircle v-if="done.has(l.id)" :size="18" weight="fill" class="shrink-0 text-accent" />
              <PhCircle v-else :size="18" weight="light" class="shrink-0 text-muted" />
              <span class="min-w-0 truncate">{{ l.title }}</span>
            </RouterLink>
          </li>
        </ol>
      </Card>
    </aside>
  </div>
</template>
