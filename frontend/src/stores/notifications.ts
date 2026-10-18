import { defineStore } from 'pinia'
import { notifications as api, realtimeTicket, type AppNotification } from '@/api/notifications'
import { connectRealtime, type RealtimeMessage } from '@/lib/realtime'

let connection: { stop(): void } | null = null

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    items: [] as AppNotification[],
    next: null as string | null,
    unread: 0,
    loaded: false,
    live: false,
    toasts: [] as AppNotification[],
  }),
  actions: {
    /** Called when a session starts: count, then the live connection. */
    async start() {
      this.stop()
      this.unread = (await api.unreadCount().catch(() => ({ count: 0 }))).count
      connection = connectRealtime({
        ticket: realtimeTicket,
        onMessage: (m) => this.apply(m),
        onStatus: (s) => (this.live = s === 'open'),
      })
    },
    stop() {
      connection?.stop()
      connection = null
      this.$reset()
    },
    async load(unreadOnly = false, more = false) {
      const cursor =
        more && this.next
          ? (new URL(this.next, location.origin).searchParams.get('cursor') ?? undefined)
          : undefined
      const page = await api.list({ unread: unreadOnly, cursor })
      this.items = more ? [...this.items, ...page.results] : page.results
      this.next = page.next
      this.loaded = true
    },
    async markRead(n: AppNotification) {
      if (n.read) return
      n.read = true
      this.unread = Math.max(0, this.unread - 1)
      await api.read(n.id)
    },
    async markAllRead() {
      await api.readAll()
      this.items.forEach((n) => (n.read = true))
      this.unread = 0
    },
    async remove(n: AppNotification) {
      await api.remove(n.id)
      this.items = this.items.filter((i) => i.id !== n.id)
      if (!n.read) this.unread = Math.max(0, this.unread - 1)
    },
    dismissToast(id: number) {
      this.toasts = this.toasts.filter((t) => t.id !== id)
    },
    /** Live events from the socket; other tabs' reads arrive here too. */
    apply({ event, data }: RealtimeMessage) {
      if (event === 'notification.created') {
        const n = data as unknown as AppNotification
        if (this.items.some((i) => i.id === n.id)) return
        if (this.loaded) this.items = [n, ...this.items]
        this.unread += 1
        this.toasts = [...this.toasts.slice(-2), n]
        setTimeout(() => this.dismissToast(n.id), 6000)
      } else if (event === 'notification.read') {
        const ids = (data.ids as number[] | undefined) ?? null
        this.items.forEach((n) => {
          if (ids === null || ids.includes(n.id)) n.read = true
        })
        void api.unreadCount().then(
          (r) => (this.unread = r.count),
          () => undefined,
        )
      }
    },
  },
})
