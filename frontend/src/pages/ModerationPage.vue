<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhShieldCheck } from '@phosphor-icons/vue'
import { moderation, REASONS, type QueueItem } from '@/api/moderation'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Tag from '@/components/ui/Tag.vue'
import { timeAgo } from '@/features/notifications/format'

const items = ref<QueueItem[]>([])
const loaded = ref(false)
const confirming = ref<string | null>(null)
const busy = ref<string | null>(null)
const reasonLabel = Object.fromEntries(REASONS.map((r) => [r.value, r.label]))
const removeLabel = { post: 'Remove post', comment: 'Remove comment', user: 'Deactivate account' }
const keyOf = (i: QueueItem) => `${i.kind}:${i.object_id}`

onMounted(async () => {
  items.value = await moderation.queue()
  loaded.value = true
})

async function resolve(item: QueueItem, action: 'remove' | 'dismiss') {
  busy.value = keyOf(item)
  try {
    await moderation.resolve(item.kind, item.object_id, action)
    items.value = items.value.filter((i) => keyOf(i) !== keyOf(item))
  } finally {
    busy.value = null
    confirming.value = null
  }
}
</script>

<template>
  <h1 class="text-3xl font-semibold">Moderation</h1>
  <p class="mt-1 text-muted">
    Open reports, oldest first. Resolving an item closes every report on it and tells the people who reported
    it.
  </p>

  <div v-if="loaded && !items.length" class="mt-16 grid justify-items-center gap-3 text-center">
    <span class="grid size-12 place-items-center rounded-full bg-success-soft text-success">
      <PhShieldCheck :size="24" weight="light" />
    </span>
    <p class="text-muted">Nothing to review. New reports appear here.</p>
  </div>

  <div class="mt-6 grid gap-4">
    <Card v-for="item in items" :key="keyOf(item)" class="grid gap-4 p-5">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="flex flex-wrap items-center gap-2">
            <Tag>{{ item.kind === 'user' ? 'person' : item.kind }}</Tag>
            <span class="font-medium">{{ item.preview?.title ?? 'Already gone' }}</span>
          </p>
          <p class="mt-1 font-mono text-xs text-muted">
            {{ item.report_count }} report{{ item.report_count === 1 ? '' : 's' }} · first
            {{ timeAgo(item.first_reported_at) }}
          </p>
        </div>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="(n, reason) in item.reasons"
            :key="reason"
            class="rounded-sm bg-danger-soft px-2 py-0.5 text-xs text-danger"
            >{{ reasonLabel[reason] }}<template v-if="n! > 1"> × {{ n }}</template></span
          >
        </div>
      </div>

      <blockquote
        v-if="item.preview?.excerpt"
        class="rounded-md bg-surface-2 p-3 text-sm break-words whitespace-pre-line text-ink"
      >
        {{ item.preview.excerpt }}
      </blockquote>
      <RouterLink
        v-if="item.preview?.url"
        :to="item.preview.url"
        class="w-fit text-sm text-accent hover:underline"
        >Open in context</RouterLink
      >

      <details class="text-sm">
        <summary class="cursor-pointer text-muted">Who reported it and why</summary>
        <ul class="mt-3 grid gap-3">
          <li v-for="r in item.reports" :key="r.id" class="flex items-start gap-3">
            <Avatar :name="r.reporter.name" :src="r.reporter.avatar" size="sm" />
            <div class="min-w-0">
              <p>
                <span class="font-medium">{{ r.reporter.name }}</span>
                <span class="ml-2 text-muted">{{ r.reason_label }} · {{ timeAgo(r.created_at) }}</span>
              </p>
              <p v-if="r.details" class="whitespace-pre-line text-ink/90">{{ r.details }}</p>
            </div>
          </li>
        </ul>
      </details>

      <div class="flex flex-wrap items-center gap-2 border-t border-line pt-4">
        <template v-if="confirming === keyOf(item)">
          <span class="text-sm text-muted">{{ removeLabel[item.kind] }}? This cannot be undone here.</span>
          <Button
            size="sm"
            variant="danger"
            :loading="busy === keyOf(item)"
            @click="resolve(item, 'remove')"
            >{{ removeLabel[item.kind] }}</Button
          >
          <Button size="sm" variant="ghost" @click="confirming = null">Back</Button>
        </template>
        <template v-else>
          <Button v-if="item.exists" size="sm" variant="danger" @click="confirming = keyOf(item)">{{
            removeLabel[item.kind]
          }}</Button>
          <Button
            size="sm"
            variant="secondary"
            :loading="busy === keyOf(item)"
            @click="resolve(item, 'dismiss')"
            >No action needed</Button
          >
        </template>
      </div>
    </Card>
  </div>
</template>
