<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { PhBookmarkSimple } from '@phosphor-icons/vue'
import { careers, labels, salary, type Job } from '@/api/careers'
import Tag from '@/components/ui/Tag.vue'
import { timeAgo } from '@/features/notifications/format'
import CompanyLogo from './CompanyLogo.vue'

const props = defineProps<{ job: Job }>()
const emit = defineEmits<{ update: [job: Job] }>()

async function toggleSave() {
  emit('update', props.job.saved ? await careers.unsave(props.job.id) : await careers.save(props.job.id))
}
</script>

<template>
  <article class="flex gap-4 rounded-lg bg-surface p-4 shadow-card ring-1 ring-line">
    <CompanyLogo :name="job.company.name" :src="job.company.logo" />
    <div class="min-w-0 flex-1">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <RouterLink
            :to="{ name: 'job', params: { id: job.id } }"
            class="font-medium text-ink hover:underline"
            >{{ job.title }}</RouterLink
          >
          <p class="text-sm text-muted">
            <RouterLink
              :to="{ name: 'company', params: { slug: job.company.slug } }"
              class="hover:text-ink"
              >{{ job.company.name }}</RouterLink
            >
            <template v-if="job.location"> · {{ job.location }}</template>
          </p>
        </div>
        <button
          type="button"
          class="grid size-9 shrink-0 cursor-pointer place-items-center rounded-md hover:bg-surface-2"
          :class="job.saved ? 'text-accent' : 'text-muted'"
          :aria-pressed="job.saved"
          :aria-label="job.saved ? `Unsave ${job.title}` : `Save ${job.title}`"
          @click="toggleSave"
        >
          <PhBookmarkSimple :size="20" :weight="job.saved ? 'fill' : 'light'" />
        </button>
      </div>
      <p class="mt-2 flex flex-wrap items-center gap-1.5">
        <Tag>{{ labels.workplace[job.workplace] }}</Tag>
        <Tag>{{ labels.type[job.employment_type] }}</Tag>
        <Tag>{{ labels.level[job.level] }}</Tag>
        <span v-if="salary(job)" class="font-mono text-xs text-ink">{{ salary(job) }}</span>
      </p>
      <p class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <span v-if="job.skill_count" :class="job.matching_skills ? 'text-accent' : ''"
          >{{ job.matching_skills }} of {{ job.skill_count }} skills match your profile</span
        >
        <span v-if="job.published_at" class="font-mono">{{ timeAgo(job.published_at) }}</span>
        <Tag v-if="job.status !== 'open'">{{ job.status }}</Tag>
        <span v-if="job.my_application" class="font-medium text-accent"
          >Applied · {{ job.my_application }}</span
        >
        <span v-if="job.applicant_count !== null" class="font-mono"
          >{{ job.applicant_count }} applicant{{ job.applicant_count === 1 ? '' : 's' }}</span
        >
      </p>
    </div>
  </article>
</template>
