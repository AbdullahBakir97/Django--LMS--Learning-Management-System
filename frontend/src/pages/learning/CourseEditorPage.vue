<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhPlus, PhPencilSimple, PhTrash, PhQuestion, PhRocketLaunch } from '@phosphor-icons/vue'
import { learning, type Course, type Lesson, type Quiz } from '@/api/learning'
import { ApiError } from '@/api/client'
import QuizEditor from '@/features/learning/QuizEditor.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'
import Tag from '@/components/ui/Tag.vue'

const props = defineProps<{ slug?: string }>()
const router = useRouter()
const course = ref<Course | null>(null)
const form = reactive({
  title: '',
  summary: '',
  description: '',
  level: 'beginner',
  language: 'en',
  price: '',
})
const errors = reactive<Record<string, string | undefined>>({})
const message = ref('')
const busy = ref(false)
const isNew = computed(() => !props.slug)

async function load() {
  if (!props.slug) return
  course.value = await learning.course(props.slug)
  Object.assign(form, {
    title: course.value.title,
    summary: course.value.summary,
    description: course.value.description,
    level: course.value.level,
    language: course.value.language,
    price: course.value.price_cents ? (course.value.price_cents / 100).toFixed(2) : '',
  })
}
watch(() => props.slug, load, { immediate: true })

async function saveCourse() {
  busy.value = true
  message.value = ''
  Object.keys(errors).forEach((k) => (errors[k] = undefined))
  const { price, ...details } = form
  const body = { ...details, price_cents: Math.round((Number(price) || 0) * 100) } as never
  try {
    if (isNew.value) {
      const created = await learning.createCourse(body)
      router.replace({ name: 'course-editor', params: { slug: created.slug } })
    } else {
      course.value = await learning.updateCourse(props.slug!, body)
      message.value = 'Saved.'
    }
  } catch (e) {
    if (e instanceof ApiError) {
      for (const k of Object.keys(form)) errors[k] = e.field(k)
      errors.price = e.field('price_cents')
    }
  } finally {
    busy.value = false
  }
}

async function publish() {
  message.value = ''
  try {
    course.value = await learning.publish(props.slug!)
    message.value = 'Published. Learners can enrol now.'
  } catch (e) {
    message.value = e instanceof ApiError ? (e.nonField ?? 'Could not publish.') : 'Network error.'
  }
}

const lessonDialog = ref(false)
const lessonForm = reactive({
  id: 0,
  title: '',
  order: 1,
  content: '',
  video_url: '',
  is_free_preview: false,
})
const lessonError = ref('')

async function openLesson(id?: number) {
  lessonError.value = ''
  if (id) {
    const l: Lesson = await learning.lesson(props.slug!, id)
    Object.assign(lessonForm, {
      id: l.id,
      title: l.title,
      order: l.order,
      content: l.content,
      video_url: l.video_url,
      is_free_preview: l.is_free_preview,
    })
  } else {
    Object.assign(lessonForm, {
      id: 0,
      title: '',
      order: (course.value?.lessons.at(-1)?.order ?? 0) + 1,
      content: '',
      video_url: '',
      is_free_preview: false,
    })
  }
  lessonDialog.value = true
}

async function saveLesson() {
  lessonError.value = ''
  const { id, ...data } = lessonForm
  try {
    if (id) await learning.updateLesson(props.slug!, id, data)
    else await learning.createLesson(props.slug!, data)
    lessonDialog.value = false
    await load()
  } catch (e) {
    lessonError.value =
      e instanceof ApiError
        ? (e.field('order') ?? e.field('title') ?? e.nonField ?? 'Could not save.')
        : 'Network error.'
  }
}

async function removeLesson(id: number) {
  await learning.deleteLesson(props.slug!, id)
  await load()
}

const quizLesson = ref<number | null>(null)
const quizInitial = ref<Quiz | null>(null)
async function openQuiz(id: number, hasQuiz: boolean) {
  quizInitial.value = hasQuiz ? await learning.quiz(id) : null
  quizLesson.value = id
}
async function closeQuiz() {
  quizLesson.value = null
  await load()
}
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <p class="font-mono text-xs text-muted">
        <RouterLink :to="{ name: 'teach' }" class="hover:text-ink">Teaching</RouterLink> /
        {{ isNew ? 'new' : course?.slug }}
      </p>
      <h1 class="mt-1 text-3xl font-semibold">{{ isNew ? 'New course' : course?.title }}</h1>
    </div>
    <div v-if="course" class="flex items-center gap-2">
      <Tag>{{ course.status }}</Tag>
      <RouterLink :to="{ name: 'course-analytics', params: { slug: course.slug } }"
        ><Button variant="secondary" size="sm">Analytics</Button></RouterLink
      >
      <RouterLink :to="{ name: 'course', params: { slug: course.slug } }"
        ><Button variant="secondary" size="sm">Preview</Button></RouterLink
      >
      <Button v-if="course.status === 'draft'" size="sm" @click="publish"
        ><PhRocketLaunch :size="16" weight="light" /> Publish</Button
      >
    </div>
  </div>
  <Alert
    v-if="message"
    class="mt-6"
    :tone="message.startsWith('Could') || message.startsWith('Add') ? 'danger' : 'success'"
    >{{ message }}</Alert
  >

  <Card class="mt-6 p-5">
    <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="saveCourse">
      <TextField v-model="form.title" label="Title" class="sm:col-span-2" :error="errors.title" required />
      <TextField
        v-model="form.summary"
        label="Summary"
        class="sm:col-span-2"
        hint="One sentence shown on the course card."
        :error="errors.summary"
      />
      <label class="grid gap-1.5 text-sm font-medium">
        Level
        <select
          v-model="form.level"
          class="h-11 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
      </label>
      <TextField v-model="form.language" label="Language code" hint="e.g. en, de, ar" />
      <TextField
        v-model="form.price"
        label="Price"
        type="number"
        :hint="`In ${(course?.currency ?? 'the site currency').toUpperCase()}. Leave empty for a free course.`"
        :error="errors.price"
      />
      <TextField
        v-model="form.description"
        label="Description (markdown)"
        textarea
        :rows="6"
        class="sm:col-span-2"
      />
      <div class="sm:col-span-2">
        <Button type="submit" :loading="busy">{{ isNew ? 'Create course' : 'Save details' }}</Button>
      </div>
    </form>
  </Card>

  <Card v-if="course" class="mt-6 p-5">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Lessons</h2>
      <Button size="sm" variant="secondary" @click="openLesson()"
        ><PhPlus :size="16" weight="light" /> Add lesson</Button
      >
    </div>
    <p v-if="!course.lessons.length" class="mt-2 text-sm text-muted">
      Add a first lesson; a course needs one to be published.
    </p>
    <ol class="mt-3 divide-y divide-line">
      <li v-for="l in course.lessons" :key="l.id" class="flex items-center gap-3 py-3">
        <span class="font-mono text-xs text-muted">{{ String(l.order).padStart(2, '0') }}</span>
        <span class="min-w-0 flex-1 truncate">{{ l.title }}</span>
        <Tag v-if="l.is_free_preview">preview</Tag>
        <Button
          size="sm"
          variant="ghost"
          :aria-label="`Quiz for ${l.title}`"
          @click="openQuiz(l.id, l.has_quiz)"
        >
          <PhQuestion :size="16" weight="light" /> {{ l.has_quiz ? 'Edit quiz' : 'Add quiz' }}
        </Button>
        <button
          type="button"
          class="grid size-9 place-items-center rounded-md text-muted hover:bg-surface-2"
          :aria-label="`Edit ${l.title}`"
          @click="openLesson(l.id)"
        >
          <PhPencilSimple :size="18" weight="light" />
        </button>
        <button
          type="button"
          class="grid size-9 place-items-center rounded-md text-muted hover:bg-danger-soft hover:text-danger"
          :aria-label="`Delete ${l.title}`"
          @click="removeLesson(l.id)"
        >
          <PhTrash :size="18" weight="light" />
        </button>
      </li>
    </ol>
  </Card>

  <Dialog v-model:open="lessonDialog" :title="lessonForm.id ? 'Edit lesson' : 'Add lesson'">
    <form class="grid gap-4" novalidate @submit.prevent="saveLesson">
      <Alert v-if="lessonError" tone="danger">{{ lessonError }}</Alert>
      <div class="grid gap-4 sm:grid-cols-[1fr_6rem]">
        <TextField v-model="lessonForm.title" label="Title" required />
        <label class="grid gap-1.5 text-sm font-medium">
          Position
          <input
            v-model.number="lessonForm.order"
            type="number"
            min="1"
            class="h-11 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
          />
        </label>
      </div>
      <TextField
        v-model="lessonForm.video_url"
        label="Video URL"
        type="url"
        hint="YouTube link or a direct .mp4 file."
      />
      <TextField v-model="lessonForm.content" label="Content (markdown)" textarea :rows="8" />
      <label class="flex items-center gap-2 text-sm"
        ><input v-model="lessonForm.is_free_preview" type="checkbox" class="accent-[var(--c-accent)]" /> Free
        preview (visible before enrolment)</label
      >
      <div class="flex justify-end"><Button type="submit">Save lesson</Button></div>
    </form>
  </Dialog>

  <Dialog :open="quizLesson !== null" title="Quiz" @update:open="quizLesson = null">
    <QuizEditor
      v-if="quizLesson !== null"
      :lesson-id="quizLesson"
      :initial="quizInitial"
      @saved="closeQuiz"
      @removed="closeQuiz"
    />
  </Dialog>
</template>
