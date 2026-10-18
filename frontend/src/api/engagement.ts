import { api } from './client'
import type { Page } from './learning'

export type ReactionKind = 'like' | 'celebrate' | 'insightful' | 'support'

export interface ReactionSummary {
  counts: Partial<Record<ReactionKind, number>>
  mine: ReactionKind | null
}

export interface Reply {
  id: number
  author: { username: string; name: string; avatar: string | null }
  body: string
  parent: number | null
  edited: boolean
  deleted: boolean
  created_at: string
  reactions: ReactionSummary
  can_edit: boolean
  can_delete: boolean
}

export interface Comment extends Reply {
  replies: Reply[]
}

/** A target is a registered kind plus an id, e.g. { key: 'lesson', id: 12 }. */
export interface Target {
  key: string
  id: number
}

const base = (t: Target) => `/engagement/${t.key}/${t.id}`

export const engagement = {
  comments: (t: Target, cursor?: string) =>
    api<Page<Comment>>(`${base(t)}/comments/${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`),
  comment: (t: Target, body: string, parent?: number) =>
    api<Comment>(`${base(t)}/comments/`, { method: 'POST', body: { body, parent } }),
  edit: (id: number, body: string) => api<Comment>(`/comments/${id}/`, { method: 'PATCH', body: { body } }),
  remove: (id: number) => api<void>(`/comments/${id}/`, { method: 'DELETE' }),
  reactions: (t: Target) => api<ReactionSummary>(`${base(t)}/reactions/`),
  react: (t: Target, kind: ReactionKind) =>
    api<ReactionSummary>(`${base(t)}/reactions/`, { method: 'PUT', body: { kind } }),
  unreact: (t: Target) => api<ReactionSummary>(`${base(t)}/reactions/`, { method: 'DELETE' }),
}
