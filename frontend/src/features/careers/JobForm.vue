<script setup lang="ts">
import { reactive, ref } from 'vue'
import { careers, labels, type Job, type JobInput } from '@/api/careers'
import { ApiError } from '@/api/client'
import TextField from '@/components/ui/TextField.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ companySlug: string; job?: Job }>()
const emit = defineEmits<{ saved: [job: Job] }>()
const j = props.job
const form = reactive({
  title: j?.title ?? '',
  description: j?.description ?? '',
  location: j?.location ?? '',
  workplace: j?.workplace ?? 'onsite',
  employment_type: j?.employment_type ?? 'full_time',
  level: j?.level ?? 'mid',
  salary_min: j?.salary_min?.toString() ?? '',
  salary_max: j?.salary_max?.toString() ?? '',
  currency: j?.currency ?? '',
  skills: (j?.skills ?? []).join(', '),
  closes_on: j?.closes_on ?? '',
})
const errors = ref<ApiError | null>(null)
const busy = ref(false)
const select =
  'h-11 w-full rounded-md bg-surface px-3 text-sm text-ink ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none'

async function submit() {
  busy.value = true
  errors.value = null
  const body: JobInput = {
    ...form,
    salary_min: form.salary_min ? Number(form.salary_min) : null,
    salary_max: form.salary_max ? Number(form.salary_max) : null,
    currency: form.currency.toUpperCase(),
    skills: form.skills
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    closes_on: form.closes_on || null,
  }
  try {
    emit(
      'saved',
      j
        ? await careers.updateJob(j.id, body)
        : await careers.createJob({ ...body, company_slug: props.companySlug }),
    )
  } catch (e) {
    if (e instanceof ApiError) errors.value = e
    else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="grid gap-4" @submit.prevent="submit">
    <TextField v-model="form.title" label="Title" required :error="errors?.field('title')" />
    <div class="grid gap-4 sm:grid-cols-3">
      <label class="grid gap-1.5 text-sm font-medium"
        >Workplace
        <select v-model="form.workplace" :class="select">
          <option v-for="(l, v) in labels.workplace" :key="v" :value="v">{{ l }}</option>
        </select>
      </label>
      <label class="grid gap-1.5 text-sm font-medium"
        >Type
        <select v-model="form.employment_type" :class="select">
          <option v-for="(l, v) in labels.type" :key="v" :value="v">{{ l }}</option>
        </select>
      </label>
      <label class="grid gap-1.5 text-sm font-medium"
        >Level
        <select v-model="form.level" :class="select">
          <option v-for="(l, v) in labels.level" :key="v" :value="v">{{ l }}</option>
        </select>
      </label>
    </div>
    <TextField v-model="form.location" label="Location" placeholder="Amman, Jordan" />
    <div class="grid gap-4 sm:grid-cols-3">
      <TextField
        v-model="form.salary_min"
        type="number"
        label="Salary from"
        :error="errors?.field('salary_min')"
      />
      <TextField
        v-model="form.salary_max"
        type="number"
        label="Salary to"
        :error="errors?.field('salary_max')"
      />
      <TextField
        v-model="form.currency"
        label="Currency"
        placeholder="JOD"
        :error="errors?.field('currency')"
      />
    </div>
    <TextField
      v-model="form.skills"
      label="Skills"
      hint="Comma separated, as people list them on profiles"
      :error="errors?.field('skills')"
    />
    <TextField
      v-model="form.description"
      textarea
      :rows="8"
      label="Description"
      hint="Markdown: the role, the team, what you offer"
      required
      :error="errors?.field('description')"
    />
    <TextField v-model="form.closes_on" type="date" label="Applications close" />
    <p v-if="errors?.nonField && !errors.problem.errors" class="text-sm text-danger" role="alert">
      {{ errors.nonField }}
    </p>
    <div class="flex justify-end">
      <Button type="submit" :loading="busy">{{ job ? 'Save' : 'Save as draft' }}</Button>
    </div>
  </form>
</template>
