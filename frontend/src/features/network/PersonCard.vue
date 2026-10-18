<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { Person } from '@/api/network'
import Avatar from '@/components/ui/Avatar.vue'

defineProps<{ person: Person; note?: string }>()
</script>

<template>
  <div class="flex items-center gap-3">
    <Avatar :name="person.name" :src="person.avatar" />
    <div class="min-w-0 flex-1">
      <RouterLink
        :to="{ name: 'profile', params: { username: person.username } }"
        class="block truncate font-medium text-ink hover:underline"
        >{{ person.name }}</RouterLink
      >
      <p class="truncate text-sm text-muted">{{ person.headline || `@${person.username}` }}</p>
      <p v-if="note" class="font-mono text-xs text-muted">{{ note }}</p>
    </div>
    <div class="flex shrink-0 items-center gap-2"><slot /></div>
  </div>
</template>
