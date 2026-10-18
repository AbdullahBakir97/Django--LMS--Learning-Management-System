<script setup lang="ts">
import { reactive, ref } from 'vue'
import { PhPlus, PhTrash } from '@phosphor-icons/vue'
import { learning, type Quiz } from '@/api/learning'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import TextField from '@/components/ui/TextField.vue'
import Alert from '@/components/ui/Alert.vue'

const props = defineProps<{ lessonId: number; initial: Quiz | null }>()
const emit = defineEmits<{ saved: []; removed: [] }>()

const blank = () => ({
  text: '',
  order: 0,
  choices: [
    { text: '', is_correct: true },
    { text: '', is_correct: false },
  ],
})
const quiz = reactive<Quiz>(
  props.initial
    ? structuredClone(props.initial)
    : { title: 'Check your understanding', pass_score: 70, questions: [blank()] },
)
const error = ref('')
const busy = ref(false)

function markCorrect(qi: number, ci: number) {
  quiz.questions[qi]!.choices.forEach((c, i) => (c.is_correct = i === ci))
}

async function save() {
  busy.value = true
  error.value = ''
  try {
    await learning.saveQuiz(props.lessonId, {
      ...quiz,
      questions: quiz.questions.map((q, i) => ({ ...q, order: i + 1 })),
    })
    emit('saved')
  } catch (e) {
    error.value =
      e instanceof ApiError ? JSON.stringify(e.problem.errors ?? e.problem.detail) : 'Network error.'
  } finally {
    busy.value = false
  }
}

async function remove() {
  await learning.deleteQuiz(props.lessonId)
  emit('removed')
}
</script>

<template>
  <form class="grid gap-5" @submit.prevent="save">
    <div class="grid gap-4 sm:grid-cols-[1fr_8rem]">
      <TextField v-model="quiz.title" label="Quiz title" required />
      <label class="grid gap-1.5 text-sm font-medium">
        Pass score (%)
        <input
          v-model.number="quiz.pass_score"
          type="number"
          min="1"
          max="100"
          class="h-11 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
        />
      </label>
    </div>
    <fieldset v-for="(q, qi) in quiz.questions" :key="qi" class="grid gap-2 rounded-md p-3 ring-1 ring-line">
      <div class="flex items-start gap-2">
        <TextField v-model="q.text" :label="`Question ${qi + 1}`" class="flex-1" required />
        <button
          type="button"
          class="mt-7 grid size-10 place-items-center rounded-md text-muted hover:bg-danger-soft hover:text-danger"
          :aria-label="`Remove question ${qi + 1}`"
          @click="quiz.questions.splice(qi, 1)"
        >
          <PhTrash :size="18" weight="light" />
        </button>
      </div>
      <div v-for="(c, ci) in q.choices" :key="ci" class="flex items-center gap-2">
        <input
          type="radio"
          :name="`correct-${qi}`"
          :checked="c.is_correct"
          :aria-label="`Mark choice ${ci + 1} correct`"
          class="accent-[var(--c-accent)]"
          @change="markCorrect(qi, ci)"
        />
        <input
          v-model="c.text"
          :placeholder="`Choice ${ci + 1}`"
          required
          class="h-10 min-w-0 flex-1 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
        />
        <button
          v-if="q.choices.length > 2"
          type="button"
          class="grid size-9 place-items-center rounded-md text-muted hover:text-danger"
          :aria-label="`Remove choice ${ci + 1}`"
          @click="q.choices.splice(ci, 1)"
        >
          <PhTrash :size="16" weight="light" />
        </button>
      </div>
      <Button
        size="sm"
        variant="ghost"
        class="justify-self-start"
        @click="q.choices.push({ text: '', is_correct: false })"
      >
        <PhPlus :size="14" weight="light" /> Add choice
      </Button>
    </fieldset>
    <Button size="sm" variant="secondary" class="justify-self-start" @click="quiz.questions.push(blank())">
      <PhPlus :size="14" weight="light" /> Add question
    </Button>
    <Alert v-if="error" tone="danger">{{ error }}</Alert>
    <div class="flex justify-between gap-2">
      <Button v-if="initial" variant="danger" @click="remove">Delete quiz</Button>
      <span v-else />
      <Button type="submit" :loading="busy" :disabled="!quiz.questions.length">Save quiz</Button>
    </div>
  </form>
</template>
