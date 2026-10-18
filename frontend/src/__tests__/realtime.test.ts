import { describe, expect, it, vi } from 'vitest'
import { backoff, connectRealtime } from '@/lib/realtime'
import { dayGroup, timeAgo } from '@/features/notifications/format'

class FakeSocket {
  static last: FakeSocket
  onopen?: () => void
  onmessage?: (e: { data: string }) => void
  onclose?: () => void
  closed = false
  readyState = 0
  sent: string[] = []
  send(data: string) {
    this.sent.push(data)
  }
  constructor(public url: string) {
    FakeSocket.last = this
  }
  close() {
    this.closed = true
  }
}

/** Let pending promise callbacks run (timers are faked in these tests). */
const flush = async () => {
  for (let i = 0; i < 5; i++) await Promise.resolve()
}

describe('realtime', () => {
  it('backs off exponentially, capped at 30 seconds', () => {
    const mid = () => 0.5
    expect([0, 1, 2, 3, 10].map((n) => backoff(n, mid))).toEqual([1000, 2000, 4000, 8000, 30000])
    expect(backoff(0, () => 0)).toBe(800)
    expect(backoff(0, () => 1)).toBe(1200)
  })

  it('connects with a ticket, delivers messages, reconnects with a fresh ticket', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const tickets = ['t1', 't2']
    const messages: unknown[] = []
    const conn = connectRealtime({
      ticket: async () => tickets.shift()!,
      onMessage: (m) => messages.push(m),
      url: (t) => `ws://x/events/?ticket=${t}`,
      socket: (u) => new FakeSocket(u) as unknown as WebSocket,
      random: () => 0.5,
    })
    await flush()
    expect(FakeSocket.last.url).toBe('ws://x/events/?ticket=t1')
    const first = FakeSocket.last
    conn.send({ type: 'typing' })
    expect(first.sent).toEqual([]) // nothing is sent before the socket opens
    first.readyState = 1
    first.onopen?.()
    conn.send({ type: 'typing', conversation: 3 })
    expect(first.sent).toEqual(['{"type":"typing","conversation":3}'])
    first.onmessage?.({ data: '{"event":"notification.created","data":{"id":1}}' })
    first.onmessage?.({ data: 'not json' })
    expect(messages).toEqual([{ event: 'notification.created', data: { id: 1 } }])

    first.onclose?.()
    await vi.advanceTimersByTimeAsync(1000)
    await flush()
    expect(FakeSocket.last.url).toBe('ws://x/events/?ticket=t2')

    conn.stop()
    expect(FakeSocket.last.closed).toBe(true)
    vi.useRealTimers()
  })
})

describe('notification formatting', () => {
  const now = new Date('2026-10-18T12:00:00Z')
  it('describes time relative to now', () => {
    expect(timeAgo('2026-10-18T11:59:50Z', now.getTime())).toBe('just now')
    expect(timeAgo('2026-10-18T11:55:00Z', now.getTime())).toBe('5 minutes ago')
    expect(timeAgo('2026-10-17T12:00:00Z', now.getTime())).toBe('yesterday')
  })
  it('groups by calendar day', () => {
    expect(dayGroup(now.toISOString(), now)).toBe('Today')
    expect(dayGroup(new Date(now.getTime() - 86_400_000).toISOString(), now)).toBe('Yesterday')
    expect(dayGroup('2026-01-01T00:00:00Z', now)).toBe('Earlier')
  })
})
