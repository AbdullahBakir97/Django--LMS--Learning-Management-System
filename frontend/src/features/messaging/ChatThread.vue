<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { PhPaperPlaneRight } from '@phosphor-icons/vue'
import { messaging, type ChatMessage, type Conversation } from '@/api/messaging'
import { ApiError } from '@/api/client'
import { bus } from '@/lib/bus'
import { sendRealtime } from '@/stores/notifications'
import { useMessagesStore } from '@/stores/messages'
import { useSessionStore } from '@/stores/session'
import Avatar from '@/components/ui/Avatar.vue'
import { dayGroup } from '@/features/notifications/format'

const props = defineProps<{ conversation: Conversation }>()
const store = useMessagesStore()
const session = useSessionStore()
const messages = ref<ChatMessage[]>([])
const older = ref<string | null>(null)
const draft = ref('')
const error = ref('')
const scroller = ref<HTMLElement | null>(null)
const editing = ref<number | null>(null)
const editText = ref('')
let lastTyping = 0

const me = computed(() => session.user?.username)
const time = new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' })
const cursorOf = (url: string | null) =>
  url ? (new URL(url, location.origin).searchParams.get('cursor') ?? undefined) : undefined

async function load() {
  const page = await messaging.messages(props.conversation.id)
  messages.value = page.results.slice().reverse()
  older.value = page.next
  await scrollDown()
  await store.open(props.conversation.id)
}
async function loadOlder() {
  const el = scroller.value
  const before = el?.scrollHeight ?? 0
  const page = await messaging.messages(props.conversation.id, cursorOf(older.value))
  messages.value = [...page.results.slice().reverse(), ...messages.value]
  older.value = page.next
  await nextTick()
  if (el) el.scrollTop = el.scrollHeight - before
}
async function scrollDown() {
  await nextTick()
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight })
}
watch(() => props.conversation.id, load, { immediate: true })

const offs = [
  bus.on('message.created', (d) => {
    const m = d as unknown as ChatMessage
    if (m.conversation !== props.conversation.id || messages.value.some((x) => x.id === m.id)) return
    const atBottom = scroller.value
      ? scroller.value.scrollHeight - scroller.value.scrollTop - scroller.value.clientHeight < 80
      : true
    messages.value.push(m)
    if (atBottom || m.sender?.username === me.value) void scrollDown()
  }),
  bus.on('message.updated', (d) => {
    const m = d as unknown as ChatMessage
    const i = messages.value.findIndex((x) => x.id === m.id)
    if (i >= 0) messages.value[i] = m
  }),
]
onUnmounted(() => {
  offs.forEach((off) => off())
  store.activeId = null
})

async function send() {
  const body = draft.value.trim()
  if (!body) return
  error.value = ''
  draft.value = ''
  try {
    const m = await messaging.send(props.conversation.id, body)
    if (!messages.value.some((x) => x.id === m.id)) messages.value.push(m)
    await scrollDown()
  } catch (e) {
    draft.value = body
    error.value =
      e instanceof ApiError
        ? (e.field('body') ?? e.nonField ?? 'Not sent.')
        : 'Not sent. Check your connection.'
  }
}
function typed() {
  if (Date.now() - lastTyping > 2500) {
    lastTyping = Date.now()
    sendRealtime({ type: 'typing', conversation: props.conversation.id })
  }
}
async function saveEdit(m: ChatMessage) {
  const updated = await messaging.edit(m.id, editText.value)
  Object.assign(m, updated)
  editing.value = null
}
async function remove(m: ChatMessage) {
  Object.assign(m, await messaging.remove(m.id))
}

const typing = computed(() => store.typing[props.conversation.id]?.name)
const seen = computed(() => {
  const last = [...messages.value].reverse().find((m) => !m.deleted)
  if (!last || last.sender?.username !== me.value || props.conversation.is_group) return false
  const other = props.conversation.people[0]?.username
  const at = other ? store.readBy[props.conversation.id]?.[other] : undefined
  return !!at && at >= last.created_at
})
const showDay = (i: number) =>
  i === 0 || dayGroup(messages.value[i - 1]!.created_at) !== dayGroup(messages.value[i]!.created_at)
const showSender = (i: number) =>
  props.conversation.is_group &&
  messages.value[i]!.sender?.username !== me.value &&
  (i === 0 || messages.value[i - 1]!.sender?.username !== messages.value[i]!.sender?.username)
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      ref="scroller"
      class="min-h-0 flex-1 overflow-y-auto px-4 py-4"
      aria-live="polite"
      aria-relevant="additions"
    >
      <div v-if="older" class="mb-4 flex justify-center">
        <button
          type="button"
          class="cursor-pointer rounded-md px-3 py-1 text-sm text-accent hover:bg-surface-2"
          @click="loadOlder"
        >
          Earlier messages
        </button>
      </div>
      <p v-if="!messages.length" class="py-10 text-center text-sm text-muted">No messages yet. Say hello.</p>
      <template v-for="(m, i) in messages" :key="m.id">
        <p v-if="showDay(i)" class="my-3 text-center font-mono text-xs text-muted">
          {{ dayGroup(m.created_at) }}
        </p>
        <p v-if="showSender(i)" class="mt-3 mb-1 ml-10 text-xs text-muted">{{ m.sender?.name }}</p>
        <div
          class="group mb-1 flex items-end gap-2"
          :class="m.sender?.username === me ? 'flex-row-reverse' : ''"
        >
          <Avatar
            v-if="m.sender?.username !== me"
            :name="m.sender?.name ?? '?'"
            :src="m.sender?.avatar"
            size="sm"
            class="!size-8"
            :class="showSender(i) || !conversation.is_group ? '' : 'invisible'"
          />
          <div
            class="max-w-[min(75%,32rem)] rounded-2xl px-3.5 py-2 text-sm break-words whitespace-pre-line"
            :class="[
              m.deleted
                ? 'bg-transparent italic text-muted ring-1 ring-line'
                : m.sender?.username === me
                  ? 'bg-accent text-accent-ink'
                  : 'bg-surface-2 text-ink',
            ]"
          >
            <template v-if="editing === m.id">
              <textarea
                v-model="editText"
                rows="2"
                aria-label="Edit message"
                class="w-64 max-w-full rounded-md bg-surface p-2 text-ink"
                @keydown.enter.exact.prevent="saveEdit(m)"
                @keydown.esc="editing = null"
              />
            </template>
            <template v-else>{{ m.deleted ? 'Message removed' : m.body }}</template>
            <span class="mt-0.5 block text-right font-mono text-[10px] opacity-70"
              >{{ time.format(new Date(m.created_at))
              }}<template v-if="m.edited && !m.deleted"> · edited</template></span
            >
          </div>
          <span
            v-if="m.sender?.username === me && !m.deleted && editing !== m.id"
            class="hidden gap-1 text-xs text-muted group-hover:flex group-focus-within:flex"
          >
            <button
              type="button"
              class="cursor-pointer hover:text-ink"
              @click="((editing = m.id), (editText = m.body))"
            >
              Edit
            </button>
            <button type="button" class="cursor-pointer hover:text-danger" @click="remove(m)">Delete</button>
          </span>
        </div>
      </template>
      <p v-if="seen" class="mt-1 text-right font-mono text-xs text-muted">Seen</p>
    </div>
    <p class="h-5 px-4 text-xs text-muted" aria-live="polite">{{ typing ? `${typing} is typing…` : '' }}</p>
    <form class="flex items-end gap-2 border-t border-line p-3" @submit.prevent="send">
      <label for="composer" class="sr-only">Message</label>
      <textarea
        id="composer"
        v-model="draft"
        rows="1"
        maxlength="4000"
        placeholder="Write a message"
        class="max-h-40 min-h-11 flex-1 resize-none rounded-xl bg-surface-2 px-3.5 py-2.5 text-sm text-ink placeholder:text-muted focus:ring-2 focus:ring-accent focus:outline-none"
        @input="typed"
        @keydown.enter.exact.prevent="send"
      />
      <button
        type="submit"
        class="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full bg-accent text-accent-ink transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="!draft.trim()"
        aria-label="Send"
      >
        <PhPaperPlaneRight :size="20" weight="fill" />
      </button>
    </form>
    <p v-if="error" class="px-4 pb-2 text-sm text-danger" role="alert">{{ error }}</p>
  </div>
</template>
