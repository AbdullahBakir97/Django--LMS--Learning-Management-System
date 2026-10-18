/** One WebSocket to /ws/events/, authenticated with a short-lived ticket.
 *  Reconnects with capped exponential backoff and jitter; a fresh ticket per attempt. */

export interface RealtimeMessage {
  event: string
  data: Record<string, unknown>
}

export interface RealtimeOptions {
  ticket: () => Promise<string>
  onMessage: (message: RealtimeMessage) => void
  onStatus?: (status: 'connecting' | 'open' | 'closed') => void
  url?: (ticket: string) => string
  socket?: (url: string) => WebSocket
  random?: () => number
}

/** Delay before reconnect attempt `n` (0-based): 1s, 2s, 4s … capped at 30s, with ±20% jitter. */
export function backoff(attempt: number, random: () => number = Math.random): number {
  const base = Math.min(30_000, 1000 * 2 ** attempt)
  return Math.round(base * (0.8 + random() * 0.4))
}

const defaultUrl = (ticket: string) => {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
  const base = import.meta.env.VITE_WS_URL ?? `${scheme}://${location.host}/ws`
  return `${base.replace(/\/$/, '')}/events/?ticket=${encodeURIComponent(ticket)}`
}

export function connectRealtime(options: RealtimeOptions) {
  const { ticket, onMessage, onStatus, url = defaultUrl, random = Math.random } = options
  const open = options.socket ?? ((u: string) => new WebSocket(u))
  let socket: WebSocket | null = null
  let attempt = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let stopped = false

  async function start() {
    if (stopped) return
    onStatus?.('connecting')
    let t: string
    try {
      t = await ticket()
    } catch {
      return retry()
    }
    if (stopped) return
    socket = open(url(t))
    socket.onopen = () => {
      attempt = 0
      onStatus?.('open')
    }
    socket.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data) as RealtimeMessage)
      } catch {
        /* ignore malformed frames */
      }
    }
    socket.onclose = () => {
      socket = null
      onStatus?.('closed')
      retry()
    }
  }

  function retry() {
    if (stopped) return
    timer = setTimeout(start, backoff(attempt++, random))
  }

  void start()
  return {
    /** Send a frame up if the socket is open; dropped otherwise (typing hints are best effort). */
    send(data: unknown) {
      if (socket?.readyState === 1) socket.send(JSON.stringify(data))
    },
    stop() {
      stopped = true
      clearTimeout(timer)
      socket?.close()
    },
  }
}
