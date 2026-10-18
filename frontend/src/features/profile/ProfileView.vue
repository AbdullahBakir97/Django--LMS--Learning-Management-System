<script setup lang="ts">
import { PhArrowSquareOut, PhMapPin, PhLink, PhThumbsUp } from '@phosphor-icons/vue'
import type { Profile } from '@/api/profiles'
import Avatar from '@/components/ui/Avatar.vue'
import Card from '@/components/ui/Card.vue'
import Tag from '@/components/ui/Tag.vue'
import { badgeIcon } from './badges'
import { dateRange, monthYear } from './format'

defineProps<{ profile: Profile; canEndorse?: boolean }>()
const emit = defineEmits<{ endorse: [skillId: number] }>()
</script>

<template>
  <header class="flex flex-wrap items-start gap-5">
    <Avatar
      :name="`${profile.user.first_name} ${profile.user.last_name}`.trim() || profile.user.username"
      :src="profile.avatar"
      size="lg"
    />
    <div class="min-w-0 flex-1">
      <h1 class="text-3xl font-semibold">
        {{ `${profile.user.first_name} ${profile.user.last_name}`.trim() || profile.user.username }}
      </h1>
      <p v-if="profile.headline" class="mt-1 text-lg text-muted">{{ profile.headline }}</p>
      <p class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
        <span class="font-mono">@{{ profile.user.username }}</span>
        <Tag>{{ profile.user.role }}</Tag>
        <span v-if="profile.location" class="inline-flex items-center gap-1"
          ><PhMapPin :size="16" weight="light" />{{ profile.location }}</span
        >
        <a
          v-if="profile.website"
          :href="profile.website"
          class="inline-flex items-center gap-1 hover:text-ink"
          target="_blank"
          rel="noopener"
          ><PhLink :size="16" weight="light" />{{ profile.website.replace(/^https?:\/\//, '') }}</a
        >
      </p>
      <div v-if="$slots.actions" class="mt-4"><slot name="actions" /></div>
    </div>
  </header>

  <p v-if="profile.bio" class="mt-6 max-w-prose whitespace-pre-line text-ink/90">{{ profile.bio }}</p>

  <div class="mt-8 grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
    <div class="grid grid-cols-[minmax(0,1fr)] content-start gap-6">
      <Card class="p-5">
        <h2 class="text-lg font-semibold">Experience</h2>
        <p v-if="!profile.experiences.length" class="mt-2 text-sm text-muted">Nothing listed yet.</p>
        <ol v-else class="mt-3 divide-y divide-line">
          <li v-for="e in profile.experiences" :key="e.id" class="py-3 first:pt-0 last:pb-0">
            <p class="font-medium">
              {{ e.title }} <span class="text-muted">· {{ e.company }}</span>
            </p>
            <p class="font-mono text-xs text-muted">
              {{ dateRange(e.start_date, e.end_date)
              }}<template v-if="e.location"> · {{ e.location }}</template>
            </p>
            <p v-if="e.description" class="mt-1 text-sm text-ink/80">{{ e.description }}</p>
          </li>
        </ol>
      </Card>
      <Card class="p-5">
        <h2 class="text-lg font-semibold">Education</h2>
        <p v-if="!profile.educations.length" class="mt-2 text-sm text-muted">Nothing listed yet.</p>
        <ol v-else class="mt-3 divide-y divide-line">
          <li v-for="e in profile.educations" :key="e.id" class="py-3 first:pt-0 last:pb-0">
            <p class="font-medium">{{ e.institution }}</p>
            <p class="text-sm text-muted">{{ [e.degree, e.field_of_study].filter(Boolean).join(', ') }}</p>
            <p class="font-mono text-xs text-muted">{{ dateRange(e.start_date, e.end_date) }}</p>
          </li>
        </ol>
      </Card>
      <Card v-if="profile.portfolio.length" class="p-5">
        <h2 class="text-lg font-semibold">Portfolio</h2>
        <ul class="mt-3 grid gap-4 sm:grid-cols-2">
          <li v-for="p in profile.portfolio" :key="p.id" class="grid content-start gap-1">
            <a
              v-if="p.url"
              :href="p.url"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1 font-medium hover:text-accent"
              >{{ p.title }}<PhArrowSquareOut :size="14" weight="light" aria-hidden="true"
            /></a>
            <p v-else class="font-medium">{{ p.title }}</p>
            <p v-if="p.completed_on" class="font-mono text-xs text-muted">{{ monthYear(p.completed_on) }}</p>
            <p v-if="p.description" class="text-sm text-ink/80">{{ p.description }}</p>
          </li>
        </ul>
      </Card>
      <slot name="recommendations" />
    </div>
    <div class="grid grid-cols-[minmax(0,1fr)] content-start gap-6">
      <Card v-if="profile.achievements.length" class="p-5">
        <h2 class="text-lg font-semibold">Badges</h2>
        <ul class="mt-3 grid gap-3">
          <li v-for="a in profile.achievements" :key="a.code" class="flex items-center gap-3">
            <span class="grid size-9 shrink-0 place-items-center rounded-md bg-accent-soft text-accent">
              <component :is="badgeIcon[a.code]" :size="20" weight="light" aria-hidden="true" />
            </span>
            <span class="min-w-0">
              <span class="block font-medium">{{ a.title }}</span>
              <span class="font-mono text-xs text-muted">{{ monthYear(a.earned_at) }}</span>
            </span>
          </li>
        </ul>
      </Card>
      <Card class="p-5">
        <h2 class="text-lg font-semibold">Skills</h2>
        <p v-if="!profile.skills.length" class="mt-2 text-sm text-muted">No skills yet.</p>
        <ul v-else class="mt-3 grid gap-2">
          <li v-for="s in profile.skills" :key="s.id" class="flex items-center justify-between gap-3">
            <span class="min-w-0">
              <span class="block truncate font-medium">{{ s.name }}</span>
              <span class="font-mono text-xs text-muted">{{ s.level }}</span>
            </span>
            <button
              v-if="canEndorse"
              type="button"
              class="inline-flex h-8 cursor-pointer items-center gap-1 rounded-md px-2 font-mono text-xs text-muted transition-colors duration-quick hover:bg-accent-soft hover:text-accent"
              :aria-label="`Endorse ${s.name}`"
              @click="emit('endorse', s.id)"
            >
              <PhThumbsUp :size="16" weight="light" />{{ s.endorsement_count }}
            </button>
            <Tag v-else>{{ s.endorsement_count }} <PhThumbsUp :size="12" weight="light" /></Tag>
          </li>
        </ul>
      </Card>
    </div>
  </div>
</template>
