<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PhBellSlash, PhChecks, PhTrash } from '@phosphor-icons/vue'
import { useNotificationsStore } from '@/stores/notifications'
import {
  notifications as api,
  type AppNotification,
  type NotificationKind,
  type NotificationPreferences,
  type PreferencesPatch,
} from '@/api/notifications'
import { ApiError } from '@/api/client'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Alert from '@/components/ui/Alert.vue'
import { dayGroup, kindIcon, timeAgo } from '@/features/notifications/format'

const store = useNotificationsStore()
const router = useRouter()
const unreadOnly = ref(false)
const loadingMore = ref(false)

const groups = computed(() => {
  const out: { label: string; items: AppNotification[] }[] = []
  for (const n of store.items) {
    const label = dayGroup(n.created_at)
    const last = out.at(-1)
    if (last?.label === label) last.items.push(n)
    else out.push({ label, items: [n] })
  }
  return out
})

watch(unreadOnly, (v) => store.load(v), { immediate: false })
onMounted(() => store.load(unreadOnly.value))

async function more() {
  loadingMore.value = true
  await store.load(unreadOnly.value, true).finally(() => (loadingMore.value = false))
}

function open(n: AppNotification) {
  void store.markRead(n)
  if (n.url) router.push(n.url)
}

/* Preferences */
const prefs = ref<NotificationPreferences | null>(null)
const prefsError = ref('')
const saved = ref(false)

// Digest times and quiet hours are kept in the browser's own time zone.
const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
const quiet = ref({ start: '', end: '' })
onMounted(async () => {
  const p = (prefs.value = await api.preferences())
  quiet.value = { start: p.quiet_start?.slice(0, 5) ?? '', end: p.quiet_end?.slice(0, 5) ?? '' }
})

async function save(patch: PreferencesPatch) {
  prefsError.value = ''
  saved.value = false
  try {
    prefs.value = await api.updatePreferences({ ...patch, timezone: zone })
    saved.value = true
  } catch (e) {
    prefsError.value = e instanceof ApiError ? (e.nonField ?? 'Could not save.') : 'Could not save.'
  }
}

function saveQuiet() {
  const { start, end } = quiet.value
  void save({ quiet_start: start || null, quiet_end: end || null })
}

function toggleKind(kind: NotificationKind, shown: boolean) {
  const muted = new Set(prefs.value?.muted_kinds ?? [])
  if (shown) muted.delete(kind)
  else muted.add(kind)
  void save({ muted_kinds: [...muted] })
}
</script>

<template>
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 class="text-3xl font-semibold">Notifications</h1>
      <p class="mt-1 text-muted">
        {{ store.unread ? `${store.unread} unread` : 'You are all caught up.' }}
        <span
          class="ml-2 inline-flex items-center gap-1.5 font-mono text-xs"
          :class="store.live ? 'text-success' : 'text-muted'"
          :title="store.live ? 'New notifications arrive as they happen' : 'Reconnecting'"
        >
          <span class="size-1.5 rounded-full" :class="store.live ? 'bg-success' : 'bg-muted'" />
          {{ store.live ? 'live' : 'offline' }}
        </span>
      </p>
    </div>
    <div class="flex items-center gap-2">
      <div class="flex rounded-md bg-surface-2 p-1 text-sm" role="group" aria-label="Filter">
        <button
          v-for="opt in [
            { v: false, label: 'All' },
            { v: true, label: 'Unread' },
          ]"
          :key="opt.label"
          type="button"
          class="h-8 cursor-pointer rounded-sm px-3 transition-colors duration-quick"
          :class="unreadOnly === opt.v ? 'bg-surface text-ink shadow-card' : 'text-muted hover:text-ink'"
          :aria-pressed="unreadOnly === opt.v"
          @click="unreadOnly = opt.v"
        >
          {{ opt.label }}
        </button>
      </div>
      <Button variant="secondary" size="sm" :disabled="!store.unread" @click="store.markAllRead()">
        <PhChecks :size="18" weight="light" /> Mark all read
      </Button>
    </div>
  </div>

  <div v-if="store.loaded && !store.items.length" class="mt-16 grid justify-items-center gap-3 text-center">
    <span class="grid size-12 place-items-center rounded-full bg-surface-2 text-muted">
      <PhBellSlash :size="24" weight="light" />
    </span>
    <p class="text-muted">
      {{ unreadOnly ? 'Nothing unread.' : 'Enrolments, endorsements and certificates will show up here.' }}
    </p>
  </div>

  <section v-for="g in groups" :key="g.label" class="mt-8">
    <h2 class="mb-2 font-mono text-xs tracking-wider text-muted uppercase">{{ g.label }}</h2>
    <Card class="divide-y divide-line overflow-hidden">
      <div
        v-for="n in g.items"
        :key="n.id"
        class="group flex items-start gap-3 p-4 transition-colors duration-quick hover:bg-surface-2"
      >
        <span
          class="grid size-9 shrink-0 place-items-center rounded-md"
          :class="n.read ? 'bg-surface-2 text-muted' : 'bg-accent-soft text-accent'"
        >
          <component :is="kindIcon[n.kind]" :size="20" weight="light" />
        </span>
        <button type="button" class="min-w-0 flex-1 cursor-pointer text-left" @click="open(n)">
          <span class="flex items-baseline gap-2">
            <span class="min-w-0 text-sm" :class="n.read ? 'text-ink' : 'font-semibold text-ink'">{{
              n.title
            }}</span>
            <span v-if="!n.read" class="size-2 shrink-0 rounded-full bg-accent" aria-label="unread" />
          </span>
          <span v-if="n.body" class="mt-0.5 block text-sm text-muted">{{ n.body }}</span>
          <time class="mt-1 block font-mono text-xs text-muted" :datetime="n.created_at">{{
            timeAgo(n.created_at)
          }}</time>
        </button>
        <button
          type="button"
          class="grid size-8 shrink-0 cursor-pointer place-items-center rounded-md text-muted opacity-100 hover:bg-surface hover:text-danger sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100"
          :aria-label="`Delete: ${n.title}`"
          @click="store.remove(n)"
        >
          <PhTrash :size="16" weight="light" />
        </button>
      </div>
    </Card>
  </section>

  <div v-if="store.next" class="mt-6 flex justify-center">
    <Button variant="ghost" :loading="loadingMore" @click="more">Show older</Button>
  </div>

  <section class="mt-14" aria-labelledby="prefs-title">
    <h2 id="prefs-title" class="text-xl font-semibold">Preferences</h2>
    <p class="mt-1 text-sm text-muted">Choose what reaches you. Changes save as you make them.</p>
    <Card v-if="prefs" class="mt-4 grid gap-5 p-5">
      <label class="flex cursor-pointer items-start justify-between gap-4">
        <span>
          <span class="block text-sm font-medium">Email for important updates</span>
          <span class="block text-sm text-muted"
            >Finished courses, application updates and interview invitations.</span
          >
        </span>
        <input
          type="checkbox"
          class="mt-1 size-4 accent-[var(--c-accent)]"
          :checked="prefs.email_enabled"
          @change="save({ email_enabled: ($event.target as HTMLInputElement).checked })"
        />
      </label>
      <div v-if="prefs.email_enabled" class="border-t border-line pt-5">
        <fieldset class="grid gap-3">
          <legend class="mb-3 text-sm font-medium">How email arrives</legend>
          <label
            v-for="opt in [
              { v: 'off', l: 'Right away', h: 'One email for each important update.' },
              { v: 'daily', l: 'Daily digest', h: 'Everything you have not read, at 08:00.' },
              { v: 'weekly', l: 'Weekly digest', h: 'Everything you have not read, Mondays at 08:00.' },
            ] as const"
            :key="opt.v"
            class="flex cursor-pointer items-start gap-3 text-sm"
          >
            <input
              type="radio"
              name="digest"
              class="mt-0.5 size-4 accent-[var(--c-accent)]"
              :checked="prefs.digest === opt.v"
              @change="save({ digest: opt.v })"
            />
            <span
              ><span class="block font-medium">{{ opt.l }}</span
              ><span class="block text-muted">{{ opt.h }}</span></span
            >
          </label>
        </fieldset>
      </div>
      <form
        v-if="prefs.email_enabled && prefs.digest === 'off'"
        class="grid gap-3 border-t border-line pt-5"
        @submit.prevent="saveQuiet"
      >
        <span>
          <span class="block text-sm font-medium">Quiet hours</span>
          <span class="block text-sm text-muted"
            >Email that would arrive in these hours waits until they end. Leave empty for none.</span
          >
        </span>
        <div class="flex flex-wrap items-end gap-3">
          <label class="grid gap-1.5 text-sm">
            From
            <input
              id="quiet-start"
              v-model="quiet.start"
              type="time"
              class="h-10 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
            />
          </label>
          <label class="grid gap-1.5 text-sm">
            Until
            <input
              id="quiet-end"
              v-model="quiet.end"
              type="time"
              class="h-10 rounded-md bg-surface px-3 ring-1 ring-line-strong focus:ring-2 focus:ring-accent focus:outline-none"
            />
          </label>
          <Button type="submit" size="sm" variant="secondary">Save quiet hours</Button>
        </div>
      </form>
      <p v-if="prefs.email_enabled" class="font-mono text-xs text-muted">Times are in {{ zone }}.</p>
      <div class="border-t border-line pt-5">
        <fieldset class="grid gap-3">
          <legend class="mb-3 text-sm font-medium">Show these notifications</legend>
          <label
            v-for="k in prefs.kinds"
            :key="k.value"
            class="flex cursor-pointer items-center gap-3 text-sm"
          >
            <input
              type="checkbox"
              class="size-4 accent-[var(--c-accent)]"
              :checked="!prefs.muted_kinds.includes(k.value)"
              @change="toggleKind(k.value, ($event.target as HTMLInputElement).checked)"
            />
            <component :is="kindIcon[k.value]" :size="18" weight="light" class="text-muted" />
            {{ k.label }}
          </label>
        </fieldset>
      </div>
      <Alert v-if="prefsError" tone="danger">{{ prefsError }}</Alert>
      <p v-else-if="saved" class="font-mono text-xs text-success" role="status">Saved</p>
    </Card>
  </section>
</template>
