<script setup lang="ts">
import { ref, useId } from 'vue'
import { community, type Group, type Post } from '@/api/community'
import { ApiError } from '@/api/client'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ groups?: Group[]; groupSlug?: string; placeholder?: string }>()
const emit = defineEmits<{ posted: [post: Post] }>()
const session = useSessionStore()
const body = ref('')
const where = ref(props.groupSlug ?? '')
const busy = ref(false)
const error = ref('')
const id = useId()

async function submit() {
  if (!body.value.trim()) return
  busy.value = true
  error.value = ''
  try {
    emit('posted', await community.createPost(body.value.trim(), where.value || null))
    body.value = ''
  } catch (e) {
    error.value =
      e instanceof ApiError ? (e.field('body') ?? e.nonField ?? 'Could not post.') : 'Network error.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="flex gap-3 rounded-lg bg-surface p-4 shadow-card ring-1 ring-line" @submit.prevent="submit">
    <Avatar :name="session.displayName" size="md" class="hidden sm:grid" />
    <div class="grid min-w-0 flex-1 gap-3">
      <label :for="id" class="sr-only">Write a post</label>
      <textarea
        :id="id"
        v-model="body"
        rows="3"
        maxlength="5000"
        :placeholder="placeholder ?? 'Share something you learned, a question, or a win'"
        class="w-full resize-y rounded-md bg-page px-3 py-2 text-sm text-ink ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
        @keydown.meta.enter="submit"
        @keydown.ctrl.enter="submit"
      />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <select
          v-if="groups?.length && !groupSlug"
          v-model="where"
          aria-label="Where to post"
          class="h-9 max-w-full min-w-0 rounded-md bg-surface px-2 text-sm text-ink ring-1 ring-line-strong"
        >
          <option value="">Your profile</option>
          <option v-for="g in groups" :key="g.slug" :value="g.slug">{{ g.name }}</option>
        </select>
        <span v-else />
        <Button type="submit" size="sm" :disabled="!body.trim()" :loading="busy">Post</Button>
      </div>
      <p v-if="error" class="text-sm text-danger" role="alert">{{ error }}</p>
    </div>
  </form>
</template>
