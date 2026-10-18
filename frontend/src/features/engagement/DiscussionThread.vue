<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { PhChatsCircle } from '@phosphor-icons/vue'
import { engagement, type Comment, type ReactionSummary, type Target } from '@/api/engagement'
import { ApiError } from '@/api/client'
import Alert from '@/components/ui/Alert.vue'
import Button from '@/components/ui/Button.vue'
import CommentComposer from './CommentComposer.vue'
import CommentItem from './CommentItem.vue'
import ReactionBar from './ReactionBar.vue'

const props = defineProps<{ target: Target; title?: string }>()
const comments = ref<Comment[]>([])
const next = ref<string | null>(null)
const reactions = ref<ReactionSummary>({ counts: {}, mine: null })
const replyingTo = ref<number | null>(null)
const error = ref('')
const composer = ref<InstanceType<typeof CommentComposer> | null>(null)

const cursorOf = (url: string | null) =>
  url ? (new URL(url, location.origin).searchParams.get('cursor') ?? undefined) : undefined

async function load(more = false) {
  const page = await engagement.comments(props.target, more ? cursorOf(next.value) : undefined)
  comments.value = more ? [...comments.value, ...page.results] : page.results
  next.value = page.next
}

watch(
  () => `${props.target.key}:${props.target.id}`,
  async () => {
    replyingTo.value = null
    await Promise.all([load(), engagement.reactions(props.target).then((r) => (reactions.value = r))])
    if (location.hash.startsWith('#comment-')) {
      await nextTick()
      document.querySelector(location.hash)?.scrollIntoView({ block: 'center' })
    }
  },
  { immediate: true },
)

async function post(body: string, parent?: number) {
  error.value = ''
  try {
    const comment = await engagement.comment(props.target, body, parent)
    if (parent) comments.value.find((c) => c.id === parent)?.replies.push(comment)
    else comments.value.push(comment)
    replyingTo.value = null
    composer.value?.reset()
  } catch (e) {
    error.value =
      e instanceof ApiError ? (e.field('body') ?? e.nonField ?? 'Could not post.') : 'Network error.'
  }
}

function removed(comment: Comment, replyId?: number) {
  if (replyId) {
    comment.replies = comment.replies.filter((r) => r.id !== replyId)
  } else if (comment.replies.length) {
    Object.assign(comment, { deleted: true, body: '', can_edit: false, can_delete: false })
  } else {
    comments.value = comments.value.filter((c) => c.id !== comment.id)
  }
}
</script>

<template>
  <section class="grid gap-5" aria-labelledby="discussion-title">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 id="discussion-title" class="flex items-center gap-2 text-lg font-semibold">
        <PhChatsCircle :size="22" weight="light" class="text-muted" /> Discussion
        <span v-if="comments.length" class="font-mono text-sm font-normal text-muted">{{
          comments.length
        }}</span>
      </h2>
      <ReactionBar :target="target" :summary="reactions" @change="reactions = $event" />
    </div>

    <CommentComposer
      ref="composer"
      :label="title ? `Ask or share something about ${title}` : 'Add to the discussion'"
      @submit="post"
    />
    <Alert v-if="error" tone="danger">{{ error }}</Alert>

    <p v-if="!comments.length" class="text-sm text-muted">No comments yet. Questions are welcome.</p>
    <ol class="grid gap-6">
      <li v-for="c in comments" :key="c.id">
        <CommentItem
          :comment="c"
          :can-reply="!c.deleted"
          @reply="replyingTo = c.id"
          @removed="removed(c)"
          @update="Object.assign(c, $event)"
        >
          <ol v-if="c.replies.length" class="mt-4 grid gap-4 border-l border-line pl-4">
            <li v-for="r in c.replies" :key="r.id">
              <CommentItem :comment="r" @removed="removed(c, r.id)" @update="Object.assign(r, $event)" />
            </li>
          </ol>
          <CommentComposer
            v-if="replyingTo === c.id"
            class="mt-3"
            :label="`Reply to ${c.author.name}`"
            submit-label="Reply"
            autofocus
            @submit="post($event, c.id)"
            cancellable
            @cancel="replyingTo = null"
          />
        </CommentItem>
      </li>
    </ol>
    <div v-if="next" class="flex justify-center">
      <Button variant="ghost" @click="load(true)">Show more comments</Button>
    </div>
  </section>
</template>
