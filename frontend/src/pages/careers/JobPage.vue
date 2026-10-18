<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { PhArrowLeft, PhCheckCircle, PhPencilSimple, PhUsers } from '@phosphor-icons/vue'
import { careers, labels, salary, type Job } from '@/api/careers'
import { ApiError } from '@/api/client'
import { renderMarkdown } from '@/features/learning/markdown'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tag from '@/components/ui/Tag.vue'
import CompanyLogo from '@/features/careers/CompanyLogo.vue'
import ApplyForm from '@/features/careers/ApplyForm.vue'
import JobForm from '@/features/careers/JobForm.vue'

const props = defineProps<{ id: string }>()
const job = ref<Job | null>(null)
const missing = ref(false)
const applying = ref(false)
const editing = ref(false)
const error = ref('')
const html = computed(() => (job.value ? renderMarkdown(job.value.description) : ''))

async function load() {
  missing.value = false
  job.value = await careers.job(Number(props.id)).catch(() => ((missing.value = true), null))
}
watch(() => props.id, load, { immediate: true })

const publish = () => run(() => careers.publish(Number(props.id)))
const close = () => run(() => careers.close(Number(props.id)))
const toggleSave = () =>
  run(() => (job.value?.saved ? careers.unsave(Number(props.id)) : careers.save(Number(props.id))))
const done = () => {
  applying.value = false
  editing.value = false
  return load()
}

async function run(fn: () => Promise<Job | unknown>) {
  error.value = ''
  try {
    await fn()
    await load()
  } catch (e) {
    error.value = e instanceof ApiError ? (e.nonField ?? 'Something went wrong.') : 'Network error.'
  }
}
</script>

<template>
  <RouterLink :to="{ name: 'jobs' }" class="inline-flex items-center gap-1 text-sm text-muted hover:text-ink">
    <PhArrowLeft :size="16" weight="light" /> Jobs
  </RouterLink>
  <Alert v-if="missing" tone="danger" class="mt-6">This job is not available.</Alert>
  <div v-else-if="job" class="mt-6 grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
    <div class="min-w-0">
      <div class="flex items-start gap-4">
        <CompanyLogo :name="job.company.name" :src="job.company.logo" size="lg" />
        <div class="min-w-0">
          <h1 class="text-3xl font-semibold">{{ job.title }}</h1>
          <p class="mt-1 text-muted">
            <RouterLink
              :to="{ name: 'company', params: { slug: job.company.slug } }"
              class="font-medium text-ink hover:underline"
              >{{ job.company.name }}</RouterLink
            >
            <template v-if="job.location"> · {{ job.location }}</template>
          </p>
        </div>
      </div>
      <p class="mt-4 flex flex-wrap items-center gap-1.5">
        <Tag>{{ labels.workplace[job.workplace] }}</Tag>
        <Tag>{{ labels.type[job.employment_type] }}</Tag>
        <Tag>{{ labels.level[job.level] }}</Tag>
        <Tag v-if="job.status !== 'open'">{{ job.status }}</Tag>
        <span v-if="salary(job)" class="ml-1 font-mono text-sm text-ink">{{ salary(job) }}</span>
      </p>
      <article class="prose-lms mt-8 max-w-prose" v-html="html" />
      <section v-if="job.skills.length" class="mt-8" aria-labelledby="skills-title">
        <h2 id="skills-title" class="text-lg font-semibold">Skills</h2>
        <p class="mt-1 text-sm text-muted">
          {{ job.matching_skills }} of {{ job.skill_count }} are on your profile.
        </p>
        <ul class="mt-3 flex flex-wrap gap-2">
          <li v-for="s in job.skills" :key="s">
            <Tag>{{ s }}</Tag>
          </li>
        </ul>
      </section>
    </div>

    <aside class="grid h-fit gap-4 lg:sticky lg:top-20">
      <Alert v-if="error" tone="danger">{{ error }}</Alert>
      <Card v-if="job.on_team" class="grid gap-3 p-5">
        <h2 class="font-semibold">Hiring</h2>
        <p class="text-sm text-muted">
          {{
            job.status === 'draft'
              ? 'Only your team can see this draft.'
              : job.status === 'open'
                ? 'Open for applications.'
                : 'Closed.'
          }}
        </p>
        <RouterLink :to="{ name: 'job-applications', params: { id: job.id } }">
          <Button variant="secondary" class="w-full"
            ><PhUsers :size="18" weight="light" /> {{ job.applicant_count }} applicants</Button
          >
        </RouterLink>
        <Button v-if="job.status !== 'open'" @click="publish">Publish</Button>
        <Button v-else variant="ghost" @click="close">Close applications</Button>
        <Button variant="ghost" @click="editing = true"
          ><PhPencilSimple :size="18" weight="light" /> Edit</Button
        >
      </Card>
      <Card v-else class="grid gap-3 p-5">
        <template v-if="job.my_application">
          <p class="flex items-center gap-2 font-medium text-accent">
            <PhCheckCircle :size="20" weight="light" /> You applied
          </p>
          <p class="text-sm text-muted">Status: {{ job.my_application }}</p>
          <RouterLink :to="{ name: 'applications' }" class="text-sm text-accent hover:underline"
            >Your applications</RouterLink
          >
        </template>
        <template v-else-if="job.status === 'open'">
          <Button @click="applying = true">Apply</Button>
          <p v-if="job.closes_on" class="text-center text-xs text-muted">Closes {{ job.closes_on }}</p>
        </template>
        <p v-else class="text-sm text-muted">This job is no longer taking applications.</p>
        <Button variant="ghost" @click="toggleSave">
          {{ job.saved ? 'Saved' : 'Save for later' }}
        </Button>
      </Card>
    </aside>

    <Dialog v-model:open="applying" :title="`Apply: ${job.title}`">
      <ApplyForm v-if="applying" :job-id="job.id" @applied="done" />
    </Dialog>
    <Dialog v-model:open="editing" title="Edit job">
      <JobForm v-if="editing" :company-slug="job.company.slug" :job="job" @saved="done" />
    </Dialog>
  </div>
</template>
