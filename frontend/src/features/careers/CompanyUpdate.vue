<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { CompanyUpdate } from '@/api/careers'
import CompanyLogo from './CompanyLogo.vue'
import { timeAgo } from '@/features/notifications/format'

defineProps<{ update: CompanyUpdate; showCompany?: boolean }>()
const emit = defineEmits<{ remove: [] }>()
</script>

<template>
  <article class="grid gap-2">
    <header class="flex items-center gap-2 text-sm">
      <CompanyLogo v-if="showCompany" :name="update.company.name" :src="update.company.logo" size="sm" />
      <RouterLink
        v-if="showCompany"
        :to="{ name: 'company', params: { slug: update.company.slug } }"
        class="font-medium hover:underline"
        >{{ update.company.name }}</RouterLink
      >
      <time class="font-mono text-xs text-muted" :datetime="update.created_at">{{
        timeAgo(update.created_at)
      }}</time>
      <span v-if="update.author && !showCompany" class="text-xs text-muted">· {{ update.author.name }}</span>
      <button
        v-if="update.can_delete"
        type="button"
        class="ml-auto h-7 cursor-pointer rounded-md px-2 text-xs text-muted hover:bg-danger-soft hover:text-danger"
        @click="emit('remove')"
      >
        Delete
      </button>
    </header>
    <p class="text-sm break-words whitespace-pre-line text-ink">{{ update.body }}</p>
  </article>
</template>
