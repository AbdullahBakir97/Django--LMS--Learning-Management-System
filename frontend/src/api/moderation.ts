import { api } from './client'
import type { Author } from './community'

export type ReportKind = 'post' | 'comment' | 'user'
export type ReportReason = 'spam' | 'harassment' | 'hate' | 'misinformation' | 'inappropriate' | 'other'

export const REASONS: { value: ReportReason; label: string }[] = [
  { value: 'spam', label: 'Spam or scam' },
  { value: 'harassment', label: 'Harassment or bullying' },
  { value: 'hate', label: 'Hate or violence' },
  { value: 'misinformation', label: 'False information' },
  { value: 'inappropriate', label: 'Sexual or inappropriate' },
  { value: 'other', label: 'Something else' },
]

export interface QueueItem {
  kind: ReportKind
  object_id: number
  exists: boolean
  preview: { title: string; excerpt: string; url: string; author: string } | null
  report_count: number
  reasons: Partial<Record<ReportReason, number>>
  reports: {
    id: number
    reporter: Author
    reason: ReportReason
    reason_label: string
    details: string
    created_at: string
  }[]
  first_reported_at: string
}

export const moderation = {
  report: (kind: ReportKind, objectId: number, reason: ReportReason, details: string) =>
    api<void>('/reports/', { method: 'POST', body: { kind, object_id: objectId, reason, details } }),
  queue: () => api<QueueItem[]>('/moderation/queue/'),
  resolve: (kind: ReportKind, objectId: number, action: 'remove' | 'dismiss', note = '') =>
    api<{ resolved: number }>(`/moderation/${kind}/${objectId}/resolve/`, {
      method: 'POST',
      body: { action, note },
    }),
}
