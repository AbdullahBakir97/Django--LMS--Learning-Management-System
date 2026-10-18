import { api } from './client'
import type { Page } from './learning'
import type { Author } from './community'

export interface ChatMessage {
  id: number
  conversation: number
  sender: Author | null
  body: string
  edited: boolean
  deleted: boolean
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  is_group: boolean
  people: Author[]
  unread: number
  last_message: ChatMessage | null
  last_message_at: string | null
}

export const messaging = {
  conversations: () => api<Conversation[]>('/conversations/'),
  conversation: (id: number) => api<Conversation>(`/conversations/${id}/`),
  start: (usernames: string[], opts: { title?: string; body?: string } = {}) =>
    api<Conversation>('/conversations/', { method: 'POST', body: { usernames, ...opts } }),
  messages: (id: number, cursor?: string) =>
    api<Page<ChatMessage>>(
      `/conversations/${id}/messages/${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`,
    ),
  send: (id: number, body: string) =>
    api<ChatMessage>(`/conversations/${id}/messages/`, { method: 'POST', body: { body } }),
  edit: (id: number, body: string) =>
    api<ChatMessage>(`/messages/${id}/`, { method: 'PATCH', body: { body } }),
  remove: (id: number) => api<ChatMessage>(`/messages/${id}/`, { method: 'DELETE' }),
  read: (id: number) => api<void>(`/conversations/${id}/read/`, { method: 'POST' }),
  unread: () => api<{ count: number }>('/conversations/unread/'),
}

/** A conversation's display name: its title, or the people in it. */
export const conversationName = (c: Conversation) =>
  c.title || c.people.map((p) => p.name).join(', ') || 'Just you'
