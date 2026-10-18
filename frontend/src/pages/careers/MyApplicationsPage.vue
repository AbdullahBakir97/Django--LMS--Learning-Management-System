<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { careers, type Application } from '@/api/careers'
import Card from '@/components/ui/Card.vue'
import Tag from '@/components/ui/Tag.vue'
import CompanyLogo from '@/features/careers/CompanyLogo.vue'
import { timeAgo } from '@/features/notifications/format'

const apps = ref<Application[]>([])
const loaded = ref(false)
const confirming = ref<number | null>(null)
onMounted(async () => {
  apps.value = (await careers.myApplications()).results
  loaded.value = true
})

async function withdraw(a: Application) {
  Object.assign(a, await careers.withdraw(a.id))
  confirming.value = null
}
const active = (a: Application) => !['withdrawn', 'hired', 'rejected'].includes(a.status)
</script>

<template>
  <h1 class="text-3xl font-semibold">Your applications</h1>
  <p class="mt-1 text-muted">Where each one stands. You are notified when a status changes.</p>
  <Card class="mt-6 divide-y divide-line">
    <div v-for="a in apps" :key="a.id" class="flex flex-wrap items-center gap-3 p-4">
      <CompanyLogo :name="a.job.company.name" :src="a.job.company.logo" size="sm" />
      <div class="min-w-0 flex-1">
        <RouterLink :to="{ name: 'job', params: { id: a.job.id } }" class="font-medium hover:underline">{{
          a.job.title
        }}</RouterLink>
        <p class="text-sm text-muted">{{ a.job.company.name }} · applied {{ timeAgo(a.created_at) }}</p>
      </div>
      <Tag :class="a.status === 'offer' || a.status === 'hired' ? '!bg-success-soft !text-success' : ''">{{
        a.status_label
      }}</Tag>
      <template v-if="active(a)">
        <button
          v-if="confirming !== a.id"
          type="button"
          class="h-8 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
          @click="confirming = a.id"
        >
          Withdraw
        </button>
        <span v-else class="inline-flex items-center gap-1 text-sm">
          <button
            type="button"
            class="h-8 cursor-pointer rounded-md bg-danger-soft px-2 text-danger"
            @click="withdraw(a)"
          >
            Withdraw
          </button>
          <button
            type="button"
            class="h-8 cursor-pointer rounded-md px-2 text-muted hover:bg-surface-2"
            @click="confirming = null"
          >
            Keep
          </button>
        </span>
      </template>
    </div>
    <p v-if="loaded && !apps.length" class="p-6 text-center text-muted">
      No applications yet.
      <RouterLink :to="{ name: 'jobs' }" class="text-accent hover:underline">Find a job</RouterLink>
    </p>
  </Card>
</template>
