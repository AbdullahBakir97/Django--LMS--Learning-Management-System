import { defineStore } from 'pinia'
import { messaging, type ChatMessage, type Conversation } from '@/api/messaging'
import { bus } from '@/lib/bus'
import { useSessionStore } from './session'

let unsubscribe: (() => void)[] = []

/** Conversations and the unread total, kept current by live events. */
export const useMessagesStore = defineStore('messages', {
  state: () => ({
    conversations: [] as Conversation[],
    loaded: false,
    unread: 0,
    activeId: null as number | null,
    typing: {} as Record<number, { name: string; until: number }>,
    readBy: {} as Record<number, Record<string, string>>,
  }),
  actions: {
    async start() {
      this.stop()
      this.unread = (await messaging.unread().catch(() => ({ count: 0 }))).count
      unsubscribe = [
        bus.on('message.created', (d) => this.received(d as unknown as ChatMessage)),
        bus.on('message.updated', (d) => this.updated(d as unknown as ChatMessage)),
        bus.on('conversation.read', (d) =>
          this.seen(d.conversation as number, d.username as string, d.at as string),
        ),
        bus.on('conversation.typing', (d) => this.typingFrom(d.conversation as number, d.name as string)),
      ]
    },
    stop() {
      unsubscribe.forEach((off) => off())
      unsubscribe = []
      this.$reset()
    },
    async load() {
      this.conversations = await messaging.conversations()
      this.loaded = true
      this.unread = this.conversations.reduce((n, c) => n + c.unread, 0)
    },
    upsert(c: Conversation) {
      this.conversations = [c, ...this.conversations.filter((x) => x.id !== c.id)]
    },
    async open(id: number) {
      this.activeId = id
      const c = this.conversations.find((x) => x.id === id)
      if (c?.unread) {
        this.unread = Math.max(0, this.unread - c.unread)
        c.unread = 0
      }
      await messaging.read(id).catch(() => undefined)
    },
    received(m: ChatMessage) {
      const mine = m.sender?.username === useSessionStore().user?.username
      delete this.typing[m.conversation]
      const c = this.conversations.find((x) => x.id === m.conversation)
      if (c) {
        c.last_message = m
        c.last_message_at = m.created_at
        this.conversations = [c, ...this.conversations.filter((x) => x.id !== c.id)]
      } else if (this.loaded) {
        void messaging.conversation(m.conversation).then((fresh) => this.upsert(fresh))
      }
      if (mine) return
      if (this.activeId === m.conversation && document.visibilityState === 'visible') {
        void messaging.read(m.conversation)
      } else {
        this.unread += 1
        if (c) c.unread += 1
      }
    },
    updated(m: ChatMessage) {
      const c = this.conversations.find((x) => x.id === m.conversation)
      if (c?.last_message?.id === m.id) c.last_message = m
    },
    seen(conversation: number, username: string, at: string) {
      this.readBy = { ...this.readBy, [conversation]: { ...this.readBy[conversation], [username]: at } }
    },
    typingFrom(conversation: number, name: string) {
      this.typing = { ...this.typing, [conversation]: { name, until: Date.now() + 4000 } }
      setTimeout(() => {
        if ((this.typing[conversation]?.until ?? 0) <= Date.now()) {
          const rest = { ...this.typing }
          delete rest[conversation]
          this.typing = rest
        }
      }, 4100)
    },
  },
})
