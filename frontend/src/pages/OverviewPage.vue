<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { insights, type Overview } from '@/api/insights'
import { money } from '@/api/learning'
import Alert from '@/components/ui/Alert.vue'
import Card from '@/components/ui/Card.vue'
import WeeklyBars from '@/features/analytics/WeeklyBars.vue'

const data = ref<Overview | null>(null)
const error = ref('')
// The biggest currency leads the tile; the table below lists every one.
const lead = computed(() => data.value?.revenue[0])
const n = (x: number) => x.toLocaleString('en')

onMounted(async () => {
  try {
    data.value = await insights.overview()
  } catch {
    error.value = 'Could not load the overview.'
  }
})
</script>

<template>
  <h1 class="text-3xl font-semibold">Overview</h1>
  <p class="mt-1 text-muted">The whole platform. “New” means the last 30 days.</p>
  <Alert v-if="error" tone="danger" class="mt-6">{{ error }}</Alert>

  <template v-else-if="data">
    <dl class="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">People</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">{{ n(data.people) }}</dd>
        <dd class="text-xs text-muted">{{ n(data.new_people) }} new</dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Enrolments</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">{{ n(data.enrolments) }}</dd>
        <dd class="text-xs text-muted">
          {{ n(data.new_enrolments) }} new · {{ data.completion_rate }}% completed
        </dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Revenue, 30 days</dt>
        <dd class="font-display text-3xl font-semibold tabular-nums">
          {{ lead ? money(lead.recent_cents, lead.currency) : '—' }}
        </dd>
        <dd class="text-xs text-muted">
          {{ lead ? `${money(lead.total_cents, lead.currency)} all time` : 'No paid orders yet' }}
        </dd>
      </Card>
      <Card class="grid gap-1 p-4">
        <dt class="text-sm text-muted">Waiting for review</dt>
        <dd
          class="font-display text-3xl font-semibold tabular-nums"
          :class="data.open_reports ? 'text-accent' : ''"
        >
          {{ data.open_reports }}
        </dd>
        <dd class="text-xs">
          <RouterLink :to="{ name: 'moderation' }" class="text-muted hover:text-ink"
            >Open the queue</RouterLink
          >
        </dd>
      </Card>
    </dl>

    <div class="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-2">
      <Card class="grid content-start gap-3 p-5">
        <h2 class="font-semibold">Sign-ups per week</h2>
        <WeeklyBars :weeks="data.weekly_signups" />
      </Card>
      <Card class="grid content-start gap-3 p-5">
        <h2 class="font-semibold">Enrolments per week</h2>
        <WeeklyBars :weeks="data.weekly_enrolments" />
      </Card>
    </div>

    <div
      class="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]"
    >
      <Card class="grid content-start gap-3 p-5">
        <div>
          <h2 class="font-semibold">Courses in demand</h2>
          <p class="text-sm text-muted">Most new enrolments first.</p>
        </div>
        <p v-if="!data.top_courses.length" class="text-sm text-muted">No enrolments yet.</p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left font-mono text-xs text-muted uppercase">
                <th class="py-2 pr-3 font-normal">Course</th>
                <th class="py-2 pr-3 text-right font-normal">New</th>
                <th class="py-2 text-right font-normal">Enrolled</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="c in data.top_courses" :key="c.slug">
                <td class="py-2 pr-3">
                  <RouterLink :to="{ name: 'course', params: { slug: c.slug } }" class="hover:text-accent">{{
                    c.title
                  }}</RouterLink>
                  <span class="block text-xs text-muted">{{ c.instructor }}</span>
                </td>
                <td class="py-2 pr-3 text-right tabular-nums">{{ n(c.new_enrolments) }}</td>
                <td class="py-2 text-right tabular-nums">{{ n(c.enrolled) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <div class="grid content-start gap-6">
        <Card class="grid content-start gap-3 p-5">
          <h2 class="font-semibold">Revenue</h2>
          <p v-if="!data.revenue.length" class="text-sm text-muted">
            No paid orders yet. Set a price on a course to start selling.
          </p>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left font-mono text-xs text-muted uppercase">
                  <th class="py-2 pr-3 font-normal">Currency</th>
                  <th class="py-2 pr-3 text-right font-normal">30 days</th>
                  <th class="py-2 pr-3 text-right font-normal">All time</th>
                  <th class="py-2 text-right font-normal">Orders</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-line">
                <tr v-for="r in data.revenue" :key="r.currency">
                  <td class="py-2 pr-3 font-mono uppercase">{{ r.currency }}</td>
                  <td class="py-2 pr-3 text-right tabular-nums">{{ money(r.recent_cents, r.currency) }}</td>
                  <td class="py-2 pr-3 text-right tabular-nums">{{ money(r.total_cents, r.currency) }}</td>
                  <td class="py-2 text-right tabular-nums">{{ n(r.orders) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
        <Card class="p-5">
          <h2 class="font-semibold">Across the platform</h2>
          <dl class="mt-3 grid grid-cols-3 items-start gap-3 text-center">
            <div class="flex flex-col-reverse">
              <dt class="text-xs text-muted">published courses</dt>
              <dd class="font-display text-2xl font-semibold tabular-nums">{{ n(data.courses) }}</dd>
            </div>
            <div class="flex flex-col-reverse">
              <dt class="text-xs text-muted">new posts</dt>
              <dd class="font-display text-2xl font-semibold tabular-nums">{{ n(data.posts) }}</dd>
            </div>
            <div class="flex flex-col-reverse">
              <dt class="text-xs text-muted">open jobs</dt>
              <dd class="font-display text-2xl font-semibold tabular-nums">{{ n(data.open_jobs) }}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  </template>
</template>
