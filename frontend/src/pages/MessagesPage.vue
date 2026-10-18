<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { PhArrowLeft, PhChatsCircle, PhNotePencil, PhUsersThree } from '@phosphor-icons/vue'
import { conversationName, type Conversation } from '@/api/messaging'
import { useMessagesStore } from '@/stores/messages'
import { useSessionStore } from '@/stores/session'
import Avatar from '@/components/ui/Avatar.vue'
import Dialog from '@/components/ui/Dialog.vue'
import { timeAgo } from '@/features/notifications/format'
import ChatThread from '@/features/messaging/ChatThread.vue'
import NewConversation from '@/features/messaging/NewConversation.vue'

const props = defineProps<{ id?: string }>()
const store = useMessagesStore()
const session = useSessionStore()
const router = useRouter()
const composing = ref(false)

onMounted(() => store.load())
const active = computed(() => store.conversations.find((c) => c.id === Number(props.id)) ?? null)

function started(c: Conversation) {
  composing.value = false
  store.upsert(c)
  router.push({ name: 'conversation', params: { id: c.id } })
}
const preview = (c: Conversation) => {
  const m = c.last_message
  if (!m) return 'No messages yet'
  if (m.deleted) return 'Message removed'
  return `${m.sender?.username === session.user?.username ? 'You: ' : c.is_group ? `${m.sender?.name.split(' ')[0]}: ` : ''}${m.body}`
}
</script>

<template>
  <h1 class="sr-only">Messages</h1>
  <div
    class="-my-4 grid h-[calc(100dvh-7rem)] grid-cols-[minmax(0,1fr)] overflow-hidden rounded-lg bg-surface ring-1 ring-line lg:grid-cols-[320px_minmax(0,1fr)]"
  >
    <aside
      class="flex min-h-0 flex-col border-line lg:border-r"
      :class="id ? 'hidden lg:flex' : 'flex'"
      aria-label="Conversations"
    >
      <div class="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 class="text-lg font-semibold">Messages</h2>
        <button
          type="button"
          class="grid size-9 cursor-pointer place-items-center rounded-md text-muted hover:bg-surface-2 hover:text-ink"
          aria-label="New conversation"
          title="New conversation"
          @click="composing = true"
        >
          <PhNotePencil :size="20" weight="light" />
        </button>
      </div>
      <ul class="min-h-0 flex-1 overflow-y-auto">
        <li v-for="c in store.conversations" :key="c.id">
          <RouterLink
            :to="{ name: 'conversation', params: { id: c.id } }"
            class="flex items-center gap-3 px-4 py-3 hover:bg-surface-2"
            :class="active?.id === c.id ? 'bg-accent-soft' : ''"
          >
            <span
              v-if="c.is_group"
              class="grid size-10 shrink-0 place-items-center rounded-full bg-surface-2 text-muted"
            >
              <PhUsersThree :size="20" weight="light" />
            </span>
            <Avatar v-else :name="c.people[0]?.name ?? '?'" :src="c.people[0]?.avatar" />
            <span class="min-w-0 flex-1">
              <span class="flex items-baseline justify-between gap-2">
                <span
                  class="truncate text-sm"
                  :class="c.unread ? 'font-semibold text-ink' : 'font-medium text-ink'"
                  >{{ conversationName(c) }}</span
                >
                <span v-if="c.last_message_at" class="shrink-0 font-mono text-[11px] text-muted">{{
                  timeAgo(c.last_message_at)
                }}</span>
              </span>
              <span class="flex items-center gap-2">
                <span class="min-w-0 flex-1 truncate text-sm" :class="c.unread ? 'text-ink' : 'text-muted'">{{
                  preview(c)
                }}</span>
                <span
                  v-if="c.unread"
                  class="grid h-5 min-w-5 place-items-center rounded-full bg-accent px-1.5 font-mono text-[11px] text-accent-ink"
                  :aria-label="`${c.unread} unread`"
                  >{{ c.unread }}</span
                >
              </span>
              <span v-if="store.typing[c.id]" class="block text-xs text-accent">typing…</span>
            </span>
          </RouterLink>
        </li>
      </ul>
      <p v-if="store.loaded && !store.conversations.length" class="p-6 text-center text-sm text-muted">
        No conversations yet.
        <button type="button" class="cursor-pointer text-accent hover:underline" @click="composing = true">
          Start one
        </button>
      </p>
    </aside>

    <section class="min-h-0 flex-col" :class="id ? 'flex' : 'hidden lg:flex'" aria-label="Conversation">
      <template v-if="active">
        <header class="flex items-center gap-3 border-b border-line px-4 py-3">
          <RouterLink
            :to="{ name: 'messages' }"
            class="grid size-9 place-items-center rounded-md text-muted hover:bg-surface-2 lg:hidden"
            aria-label="Back to conversations"
          >
            <PhArrowLeft :size="20" weight="light" />
          </RouterLink>
          <div class="min-w-0">
            <p class="truncate font-semibold">{{ conversationName(active) }}</p>
            <p v-if="!active.is_group && active.people[0]" class="truncate text-xs text-muted">
              <RouterLink
                :to="{ name: 'profile', params: { username: active.people[0].username } }"
                class="hover:underline"
                >@{{ active.people[0].username }}</RouterLink
              >
            </p>
            <p v-else class="truncate text-xs text-muted">{{ active.people.length + 1 }} people</p>
          </div>
        </header>
        <ChatThread :key="active.id" :conversation="active" class="min-h-0 flex-1" />
      </template>
      <div
        v-else
        class="grid flex-1 place-content-center justify-items-center gap-2 p-6 text-center text-muted"
      >
        <PhChatsCircle :size="36" weight="light" />
        <p>Pick a conversation, or start a new one.</p>
      </div>
    </section>
  </div>

  <Dialog v-model:open="composing" title="New conversation">
    <NewConversation v-if="composing" @started="started" />
  </Dialog>
</template>
