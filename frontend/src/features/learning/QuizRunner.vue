<script setup lang="ts">
import { reactive, ref } from 'vue'
import { learning, type Quiz, type QuizResult } from '@/api/learning'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const props = defineProps<{ lessonId: number; quiz: Quiz }>()
const emit = defineEmits<{ passed: [] }>()
const answers = reactive<Record<number, number>>({})
const result = ref<QuizResult | null>(null)
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    result.value = await learning.submitQuiz(props.lessonId, answers)
    if (result.value.passed) emit('passed')
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Could not submit.') : 'Network error. Try again.'
  } finally {
    busy.value = false
  }
}

function retry() {
  result.value = null
  Object.keys(answers).forEach((k) => delete answers[Number(k)])
}
</script>

<template>
  <form class="grid gap-6" @submit.prevent="submit">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="text-xl font-semibold">{{ quiz.title }}</h2>
      <span class="shrink-0 font-mono text-xs whitespace-nowrap text-muted"
        >pass at {{ quiz.pass_score }}%</span
      >
    </div>
    <fieldset v-for="(q, i) in quiz.questions" :key="q.id" class="grid gap-2" :disabled="!!result">
      <legend class="mb-2 font-medium">
        <span class="font-mono text-muted">{{ i + 1 }}.</span> {{ q.text }}
      </legend>
      <label
        v-for="choice in q.choices"
        :key="choice.id"
        class="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 ring-1 ring-line transition-colors duration-quick hover:bg-surface-2 has-checked:bg-accent-soft has-checked:ring-accent"
      >
        <input
          v-model="answers[q.id!]"
          type="radio"
          :name="`q-${q.id}`"
          :value="choice.id"
          class="accent-[var(--c-accent)]"
        />
        {{ choice.text }}
      </label>
    </fieldset>
    <Alert v-if="error" tone="danger">{{ error }}</Alert>
    <Alert v-if="result" :tone="result.passed ? 'success' : 'danger'">
      You scored {{ result.score }}%.
      {{ result.passed ? 'Passed.' : `You need ${result.pass_score}% to pass.` }}
    </Alert>
    <div class="flex gap-2">
      <Button
        v-if="!result"
        type="submit"
        :loading="busy"
        :disabled="Object.keys(answers).length < quiz.questions.length"
        >Submit answers</Button
      >
      <Button v-else-if="!result.passed" variant="secondary" @click="retry">Try again</Button>
    </div>
  </form>
</template>
