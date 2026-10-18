<script setup lang="ts">
import type { Recommendation } from '@/api/network'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import Tag from '@/components/ui/Tag.vue'

defineProps<{ items: Recommendation[]; manage?: boolean }>()
const emit = defineEmits<{
  status: [id: number, status: 'published' | 'hidden']
  remove: [id: number]
}>()
</script>

<template>
  <ol class="divide-y divide-line">
    <li v-for="r in items" :key="r.id" class="grid grid-cols-[minmax(0,1fr)] gap-2 py-4 first:pt-0 last:pb-0">
      <div class="flex items-center gap-3">
        <Avatar :name="r.author.name" :src="r.author.avatar" size="sm" />
        <div class="min-w-0 flex-1">
          <RouterLink
            :to="{ name: 'profile', params: { username: r.author.username } }"
            class="font-medium hover:underline"
            >{{ r.author.name }}</RouterLink
          >
          <p class="truncate text-sm text-muted">{{ r.relationship }}</p>
        </div>
        <Tag v-if="manage && r.status !== 'published'">{{ r.status }}</Tag>
      </div>
      <blockquote class="max-w-prose whitespace-pre-line text-ink/90">{{ r.body }}</blockquote>
      <div v-if="manage" class="flex flex-wrap gap-2">
        <Button v-if="r.status !== 'published'" size="sm" @click="emit('status', r.id, 'published')"
          >Show on my profile</Button
        >
        <Button
          v-if="r.status !== 'hidden'"
          size="sm"
          variant="secondary"
          @click="emit('status', r.id, 'hidden')"
          >Hide</Button
        >
        <Button size="sm" variant="ghost" @click="emit('remove', r.id)">Delete</Button>
      </div>
    </li>
  </ol>
</template>
