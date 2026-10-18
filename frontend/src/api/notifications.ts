import { api } from './client'
import type { Page } from './learning'

export type NotificationKind = 'enrolment' | 'course_completed' | 'endorsement'

export interface AppNotification {
  id: number
  kind: NotificationKind
  title: string
  body: string
  url: string
  actor: { username: string; name: string } | null
  read: boolean
  created_at: string
}

export interface NotificationPreferences {
  email_enabled: boolean
  muted_kinds: NotificationKind[]
  kinds: { value: NotificationKind; label: string }[]
}

export const notifications = {
  list: (params: { unread?: boolean; cursor?: string } = {}) => {
    const q = new URLSearchParams()
    if (params.unread) q.set('unread', 'true')
    if (params.cursor) q.set('cursor', params.cursor)
    return api<Page<AppNotification>>(`/notifications/?${q}`)
  },
  unreadCount: () => api<{ count: number }>('/notifications/unread-count/'),
  read: (id: number) => api<AppNotification>(`/notifications/${id}/read/`, { method: 'POST' }),
  readAll: () => api<{ count: number }>('/notifications/read-all/', { method: 'POST' }),
  remove: (id: number) => api<void>(`/notifications/${id}/`, { method: 'DELETE' }),
  preferences: () => api<NotificationPreferences>('/notifications/preferences/'),
  updatePreferences: (body: Partial<Pick<NotificationPreferences, 'email_enabled' | 'muted_kinds'>>) =>
    api<NotificationPreferences>('/notifications/preferences/', { method: 'PATCH', body }),
}

export const realtimeTicket = () =>
  api<{ ticket: string }>('/realtime/ticket/', { method: 'POST' }).then((r) => r.ticket)
