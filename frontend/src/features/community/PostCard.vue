<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhChatCircle, PhLockSimple, PhRepeat, PhUsersThree } from '@phosphor-icons/vue'
import { community, type Post } from '@/api/community'
import Avatar from '@/components/ui/Avatar.vue'
import ReactionBar from '@/features/engagement/ReactionBar.vue'
import DiscussionThread from '@/features/engagement/DiscussionThread.vue'
import CommentComposer from '@/features/engagement/CommentComposer.vue'
import { timeAgo } from '@/features/notifications/format'
import PostImages from './PostImages.vue'
import ReportButton from '@/features/moderation/ReportButton.vue'
import { useSessionStore } from '@/stores/session'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{ post: Post; openComments?: boolean; hideGroup?: boolean }>()
const emit = defineEmits<{ update: [patch: Partial<Post>]; removed: [] }>()
const showComments = ref(props.openComments ?? false)
const session = useSessionStore()
const editing = ref(false)
const confirming = ref(false)

async function save(body: string) {
  const updated = await community.editPost(props.post.id, body)
  emit('update', { body: updated.body, edited: true })
  editing.value = false
}

// Share the original, not the share: the server does the same.
const original = () => props.post.shared_from ?? props.post
const sharing = ref(false)
const shareNote = ref('')
const shared = ref(false)
const canShare = () => original().group?.privacy !== 'private'

async function share() {
  await community.sharePost(original().id, shareNote.value.trim())
  emit('update', { share_count: props.post.share_count + 1 })
  sharing.value = false
  shareNote.value = ''
  shared.value = true
}

async function remove() {
  await community.deletePost(props.post.id)
  emit('removed')
}
</script>

<template>
  <article
    class="rounded-lg bg-surface shadow-card ring-1 ring-line"
    :aria-label="`Post by ${post.author.name}`"
  >
    <header class="flex items-start gap-3 p-4 pb-0">
      <Avatar :name="post.author.name" :src="post.author.avatar" />
      <div class="min-w-0 flex-1">
        <p class="flex flex-wrap items-baseline gap-x-2 text-sm">
          <RouterLink
            :to="{ name: 'profile', params: { username: post.author.username } }"
            class="font-medium text-ink hover:underline"
            >{{ post.author.name }}</RouterLink
          >
          <template v-if="post.group && !hideGroup">
            <span class="text-muted">in</span>
            <RouterLink
              :to="{ name: 'group', params: { slug: post.group.slug } }"
              class="inline-flex items-center gap-1 font-medium text-ink hover:underline"
            >
              <component
                :is="post.group.privacy === 'private' ? PhLockSimple : PhUsersThree"
                :size="14"
                weight="light"
                class="text-muted"
              />{{ post.group.name }}</RouterLink
            >
          </template>
        </p>
        <RouterLink
          :to="{ name: 'post', params: { id: post.id } }"
          class="font-mono text-xs text-muted hover:underline"
        >
          <time :datetime="post.created_at">{{ timeAgo(post.created_at) }}</time>
          <span v-if="post.edited"> · edited</span>
        </RouterLink>
      </div>
    </header>

    <div class="px-4 pt-3">
      <CommentComposer
        v-if="editing"
        label="Edit your post"
        submit-label="Save"
        :initial="post.body"
        cancellable
        @submit="save"
        @cancel="editing = false"
      />
      <p v-else-if="post.body" class="text-[15px] leading-relaxed break-words whitespace-pre-line text-ink">
        {{ post.body }}
      </p>
      <PostImages :images="post.images" class="mt-3" />
      <RouterLink
        v-if="post.shared_from"
        :to="{ name: 'post', params: { id: post.shared_from.id } }"
        class="mt-3 grid gap-2 rounded-md p-3 ring-1 ring-line hover:bg-surface-2"
      >
        <span class="flex items-center gap-2 text-sm">
          <Avatar :name="post.shared_from.author.name" :src="post.shared_from.author.avatar" size="sm" />
          <span class="font-medium">{{ post.shared_from.author.name }}</span>
          <time class="font-mono text-xs text-muted" :datetime="post.shared_from.created_at">{{
            timeAgo(post.shared_from.created_at)
          }}</time>
        </span>
        <span
          v-if="post.shared_from.body"
          class="line-clamp-6 text-sm break-words whitespace-pre-line text-ink"
          >{{ post.shared_from.body }}</span
        >
        <PostImages :images="post.shared_from.images" />
      </RouterLink>
    </div>

    <footer class="flex flex-wrap items-center gap-1 px-4 py-3">
      <ReactionBar
        :target="{ key: 'post', id: post.id }"
        :summary="post.reactions"
        @change="emit('update', { reactions: $event })"
      />
      <button
        type="button"
        class="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-md px-2.5 text-sm text-muted hover:bg-surface-2 hover:text-ink"
        :aria-expanded="showComments"
        @click="showComments = !showComments"
      >
        <PhChatCircle :size="16" weight="light" />
        {{
          post.comment_count
            ? `${post.comment_count} comment${post.comment_count === 1 ? '' : 's'}`
            : 'Comment'
        }}
      </button>
      <button
        v-if="canShare()"
        type="button"
        class="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-md px-2.5 text-sm text-muted hover:bg-surface-2 hover:text-ink"
        :aria-expanded="sharing"
        @click="sharing = !sharing"
      >
        <PhRepeat :size="16" weight="light" />
        {{ post.share_count ? `${post.share_count} share${post.share_count === 1 ? '' : 's'}` : 'Share' }}
      </button>
      <span v-if="shared" class="text-sm text-success" role="status">Shared to your profile</span>
      <span class="flex-1" />
      <ReportButton v-if="post.author.username !== session.user?.username" kind="post" :object-id="post.id" />
      <button
        v-if="post.can_edit && !editing"
        type="button"
        class="h-8 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
        @click="editing = true"
      >
        Edit
      </button>
      <template v-if="post.can_delete">
        <button
          v-if="!confirming"
          type="button"
          class="h-8 cursor-pointer rounded-md px-2 text-sm text-muted hover:bg-danger-soft hover:text-danger"
          @click="confirming = true"
        >
          Delete
        </button>
        <span v-else class="inline-flex items-center gap-1 text-sm" role="group" aria-label="Confirm delete">
          <span class="text-muted">Delete post?</span>
          <button
            type="button"
            class="h-8 cursor-pointer rounded-md bg-danger-soft px-2 text-danger"
            @click="remove"
          >
            Delete
          </button>
          <button
            type="button"
            class="h-8 cursor-pointer rounded-md px-2 text-muted hover:bg-surface-2"
            @click="confirming = false"
          >
            Keep
          </button>
        </span>
      </template>
    </footer>

    <form v-if="sharing" class="grid gap-2 border-t border-line p-4" @submit.prevent="share">
      <label :for="`share-${post.id}`" class="text-sm font-medium">Share to your profile</label>
      <textarea
        :id="`share-${post.id}`"
        v-model="shareNote"
        rows="2"
        maxlength="5000"
        placeholder="Add a thought (optional)"
        class="w-full resize-y rounded-md bg-page px-3 py-2 text-sm text-ink ring-1 ring-line placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
      />
      <div class="flex gap-2">
        <Button type="submit" size="sm">Share</Button>
        <Button type="button" size="sm" variant="ghost" @click="sharing = false">Cancel</Button>
      </div>
    </form>
    <div v-if="showComments" class="border-t border-line p-4">
      <DiscussionThread :target="{ key: 'post', id: post.id }" bare />
    </div>
  </article>
</template>
