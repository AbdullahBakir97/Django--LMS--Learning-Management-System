<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { PhArrowLeft, PhFilePdf } from '@phosphor-icons/vue'
import { careers, type Application, type ApplicationStatus, type Job } from '@/api/careers'
import { apiBlob, ApiError } from '@/api/client'
import Alert from '@/components/ui/Alert.vue'
import Avatar from '@/components/ui/Avatar.vue'
import Card from '@/components/ui/Card.vue'
import { timeAgo } from '@/features/notifications/format'

const props = defineProps<{ id: string }>()
const job = ref<Job | null>(null)
const apps = ref<Application[]>([])
const error = ref('')
const open = ref<number | null>(null)
const statuses: { v: ApplicationStatus; l: string }[] = [
  { v: 'submitted', l: 'Submitted' },
  { v: 'reviewing', l: 'In review' },
  { v: 'interview', l: 'Interviewing' },
  { v: 'offer', l: 'Offer' },
  { v: 'hired', l: 'Hired' },
  { v: 'rejected', l: 'Not selected' },
]

watch(
  () => props.id,
  async (id) => {
    error.value = ''
    try {
      job.value = await careers.job(Number(id))
      apps.value = (await careers.jobApplications(Number(id))).results
    } catch (e) {
      error.value =
        e instanceof ApiError && e.problem.status === 403
          ? 'Only the hiring team can see applications.'
          : 'Could not load applications.'
    }
  },
  { immediate: true },
)

async function setStatus(a: Application, status: ApplicationStatus) {
  const updated = await careers.setStatus(a.id, status)
  Object.assign(a, updated)
}

async function resume(a: Application) {
  const blob = await apiBlob(a.resume_url)
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
</script>

<template>
  <RouterLink
    v-if="job"
    :to="{ name: 'job', params: { id: job.id } }"
    class="inline-flex items-center gap-1 text-sm text-muted hover:text-ink"
  >
    <PhArrowLeft :size="16" weight="light" /> {{ job.title }}
  </RouterLink>
  <h1 class="mt-4 text-3xl font-semibold">Applicants</h1>
  <p v-if="job" class="mt-1 text-muted">
    {{ job.title }} at {{ job.company.name }} · {{ apps.length }} so far
  </p>
  <Alert v-if="error" tone="danger" class="mt-6">{{ error }}</Alert>

  <Card v-else class="mt-6 divide-y divide-line">
    <div v-for="a in apps" :key="a.id" class="grid gap-3 p-4">
      <div class="flex flex-wrap items-center gap-3">
        <Avatar :name="a.applicant.name" :src="a.applicant.avatar" />
        <div class="min-w-0 flex-1">
          <RouterLink
            :to="{ name: 'profile', params: { username: a.applicant.username } }"
            class="font-medium hover:underline"
            >{{ a.applicant.name }}</RouterLink
          >
          <p class="truncate text-sm text-muted">{{ a.applicant_headline || `@${a.applicant.username}` }}</p>
        </div>
        <span class="font-mono text-xs text-muted">{{ timeAgo(a.created_at) }}</span>
        <button
          type="button"
          class="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-md px-3 text-sm ring-1 ring-line-strong hover:bg-surface-2"
          @click="resume(a)"
        >
          <PhFilePdf :size="18" weight="light" /> Résumé
        </button>
        <span v-if="a.status === 'withdrawn'" class="text-sm text-muted">Withdrawn</span>
        <select
          v-else
          :value="a.status"
          :aria-label="`Status for ${a.applicant.name}`"
          class="h-9 rounded-md bg-surface px-2 text-sm ring-1 ring-line-strong"
          @change="setStatus(a, ($event.target as HTMLSelectElement).value as ApplicationStatus)"
        >
          <option v-for="s in statuses" :key="s.v" :value="s.v">{{ s.l }}</option>
        </select>
      </div>
      <div v-if="a.cover_letter">
        <button
          type="button"
          class="cursor-pointer text-sm text-accent hover:underline"
          @click="open = open === a.id ? null : a.id"
        >
          {{ open === a.id ? 'Hide' : 'Read' }} cover letter
        </button>
        <p v-if="open === a.id" class="mt-2 max-w-prose text-sm whitespace-pre-line text-ink">
          {{ a.cover_letter }}
        </p>
      </div>
    </div>
    <p v-if="!apps.length" class="p-6 text-center text-muted">No applications yet.</p>
  </Card>
</template>
