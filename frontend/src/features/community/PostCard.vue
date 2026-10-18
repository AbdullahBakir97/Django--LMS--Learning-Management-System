<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { PhChatCircle, PhLockSimple, PhUsersThree } from '@phosphor-icons/vue'
import { community, type Post } from '@/api/community'
import Avatar from '@/components/ui/Avatar.vue'
import ReactionBar from '@/features/engagement/ReactionBar.vue'
import DiscussionThread from '@/features/engagement/DiscussionThread.vue'
import CommentComposer from '@/features/engagement/CommentComposer.vue'
import { timeAgo } from '@/features/notifications/format'

const props = defineProps<{ post: Post; openComments?: boolean; hideGroup?: boolean }>()
const emit = defineEmits<{ update: [patch: Partial<Post>]; removed: [] }>()
const showComments = ref(props.openComments ?? false)
const editing = ref(false)
const confirming = ref(false)

async function save(body: string) {
  const updated = await community.editPost(props.post.id, body)
  emit('update', { body: updated.body, edited: true })
  editing.value = false
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
      <p v-else class="text-[15px] leading-relaxed break-words whitespace-pre-line text-ink">
        {{ post.body }}
      </p>
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
      <span class="flex-1" />
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

    <div v-if="showComments" class="border-t border-line p-4">
      <DiscussionThread :target="{ key: 'post', id: post.id }" bare />
    </div>
  </article>
</template>
