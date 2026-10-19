<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { engagement, type Reply } from '@/api/engagement'
import Avatar from '@/components/ui/Avatar.vue'
import { timeAgo } from '@/features/notifications/format'
import ReactionBar from './ReactionBar.vue'
import CommentComposer from './CommentComposer.vue'
import ReportButton from '@/features/moderation/ReportButton.vue'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ comment: Reply; canReply?: boolean }>()
const emit = defineEmits<{ reply: []; removed: []; update: [patch: Partial<Reply>] }>()
const editing = ref(false)
const session = useSessionStore()
const confirming = ref(false)

async function save(body: string) {
  const updated = await engagement.edit(props.comment.id, body)
  emit('update', { body: updated.body, edited: true })
  editing.value = false
}

async function remove() {
  await engagement.remove(props.comment.id)
  emit('removed')
}
</script>

<template>
  <article :id="`comment-${comment.id}`" class="flex scroll-mt-24 gap-3">
    <Avatar :name="comment.deleted ? '?' : comment.author.name" :src="comment.author.avatar" size="sm" />
    <div class="min-w-0 flex-1">
      <p v-if="comment.deleted" class="py-1 text-sm text-muted italic">This comment was removed.</p>
      <template v-else>
        <p class="flex flex-wrap items-baseline gap-x-2 text-sm">
          <RouterLink
            :to="{ name: 'profile', params: { username: comment.author.username } }"
            class="font-medium text-ink hover:underline"
            >{{ comment.author.name }}</RouterLink
          >
          <time class="font-mono text-xs text-muted" :datetime="comment.created_at">{{
            timeAgo(comment.created_at)
          }}</time>
          <span v-if="comment.edited" class="font-mono text-xs text-muted">edited</span>
        </p>
        <CommentComposer
          v-if="editing"
          class="mt-2"
          label="Edit your comment"
          submit-label="Save"
          :initial="comment.body"
          @submit="save"
          cancellable
          @cancel="editing = false"
        />
        <p v-else class="mt-1 text-sm break-words whitespace-pre-line text-ink">{{ comment.body }}</p>
        <div v-if="!editing" class="mt-2 flex flex-wrap items-center gap-1">
          <ReactionBar
            :target="{ key: 'comment', id: comment.id }"
            :summary="comment.reactions"
            compact
            @change="emit('update', { reactions: $event })"
          />
          <button
            v-if="canReply"
            type="button"
            class="h-7 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
            @click="emit('reply')"
          >
            Reply
          </button>
          <ReportButton
            v-if="comment.author.username !== session.user?.username"
            kind="comment"
            :object-id="comment.id"
            compact
          />
          <button
            v-if="comment.can_edit"
            type="button"
            class="h-7 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
            @click="editing = true"
          >
            Edit
          </button>
          <template v-if="comment.can_delete">
            <button
              v-if="!confirming"
              type="button"
              class="h-7 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-danger-soft hover:text-danger"
              @click="confirming = true"
            >
              Delete
            </button>
            <span
              v-else
              class="inline-flex items-center gap-1 text-sm"
              role="group"
              aria-label="Confirm delete"
            >
              <span class="text-muted">Delete this comment?</span>
              <button
                type="button"
                class="h-7 cursor-pointer rounded-md bg-danger-soft px-2 text-danger"
                @click="remove"
              >
                Delete
              </button>
              <button
                type="button"
                class="h-7 cursor-pointer rounded-md px-2 text-muted hover:bg-surface-2"
                @click="confirming = false"
              >
                Keep
              </button>
            </span>
          </template>
        </div>
      </template>
      <slot />
    </div>
  </article>
</template>
