import { api } from './client'
import type { Page } from './learning'
import type { ReactionSummary } from './engagement'

export interface Author {
  username: string
  name: string
  avatar: string | null
}

export type Privacy = 'public' | 'private'

export interface Group {
  id: number
  slug: string
  name: string
  description: string
  privacy: Privacy
  owner: Author
  member_count: number
  my_status: 'active' | 'pending' | null
  my_role: 'owner' | 'admin' | 'member' | null
  created_at: string
}

export interface Member {
  user_id: number
  person: Author
  headline: string
  role: 'owner' | 'admin' | 'member'
  status: 'active' | 'pending'
  created_at: string
}

export interface Post {
  id: number
  author: Author
  group: { slug: string; name: string; privacy: Privacy } | null
  body: string
  edited: boolean
  created_at: string
  reactions: ReactionSummary
  comment_count: number
  can_edit: boolean
  can_delete: boolean
}

export interface CommunityEvent {
  id: number
  title: string
  description: string
  starts_at: string
  ends_at: string
  location: string
  online_url: string
  capacity: number | null
  host: Author
  group: { slug: string; name: string; privacy: Privacy } | null
  going_count: number
  my_status: 'going' | 'interested' | null
  can_edit: boolean
  created_at: string
}

export type EventInput = Pick<
  CommunityEvent,
  'title' | 'description' | 'starts_at' | 'ends_at' | 'location' | 'online_url' | 'capacity'
> & { group_slug?: string | null }

const qs = (params: Record<string, string | undefined>) => {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v) q.set(k, v)
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const community = {
  feed: (cursor?: string) => api<Page<Post>>(`/posts/${qs({ cursor })}`),
  postsBy: (username: string, cursor?: string) =>
    api<Page<Post>>(`/posts/${qs({ author: username, cursor })}`),
  post: (id: number) => api<Post>(`/posts/${id}/`),
  createPost: (body: string, groupSlug?: string | null) =>
    api<Post>('/posts/', { method: 'POST', body: { body, group_slug: groupSlug ?? null } }),
  editPost: (id: number, body: string) => api<Post>(`/posts/${id}/`, { method: 'PATCH', body: { body } }),
  deletePost: (id: number) => api<void>(`/posts/${id}/`, { method: 'DELETE' }),

  groups: (params: { search?: string; mine?: boolean; cursor?: string } = {}) =>
    api<Page<Group>>(
      `/groups/${qs({ search: params.search, mine: params.mine ? 'true' : undefined, cursor: params.cursor })}`,
    ),
  group: (slug: string) => api<Group>(`/groups/${slug}/`),
  createGroup: (body: Pick<Group, 'name' | 'description' | 'privacy'>) =>
    api<Group>('/groups/', { method: 'POST', body }),
  updateGroup: (slug: string, body: Partial<Pick<Group, 'name' | 'description' | 'privacy'>>) =>
    api<Group>(`/groups/${slug}/`, { method: 'PATCH', body }),
  deleteGroup: (slug: string) => api<void>(`/groups/${slug}/`, { method: 'DELETE' }),
  join: (slug: string) => api<Group>(`/groups/${slug}/join/`, { method: 'POST' }),
  leave: (slug: string) => api<Group>(`/groups/${slug}/leave/`, { method: 'POST' }),
  members: (slug: string, status: 'active' | 'pending' = 'active') =>
    api<Member[]>(`/groups/${slug}/members/?status=${status}`),
  approve: (slug: string, userId: number) =>
    api<Member>(`/groups/${slug}/members/${userId}/approve/`, { method: 'POST' }),
  removeMember: (slug: string, userId: number) =>
    api<void>(`/groups/${slug}/members/${userId}/`, { method: 'DELETE' }),
  setRole: (slug: string, userId: number, role: 'admin' | 'member') =>
    api<Member>(`/groups/${slug}/members/${userId}/`, { method: 'PATCH', body: { role } }),
  groupPosts: (slug: string, cursor?: string) => api<Page<Post>>(`/groups/${slug}/posts/${qs({ cursor })}`),

  events: (params: { when?: 'upcoming' | 'past'; group?: string; attending?: boolean } = {}) =>
    api<Page<CommunityEvent>>(
      `/events/${qs({ when: params.when, group: params.group, attending: params.attending ? 'true' : undefined })}`,
    ),
  event: (id: number) => api<CommunityEvent>(`/events/${id}/`),
  createEvent: (body: EventInput) => api<CommunityEvent>('/events/', { method: 'POST', body }),
  deleteEvent: (id: number) => api<void>(`/events/${id}/`, { method: 'DELETE' }),
  rsvp: (id: number, status: 'going' | 'interested') =>
    api<CommunityEvent>(`/events/${id}/rsvp/`, { method: 'PUT', body: { status } }),
  cancelRsvp: (id: number) => api<CommunityEvent>(`/events/${id}/rsvp/`, { method: 'DELETE' }),
}

export const cursorOf = (url: string | null) =>
  url ? (new URL(url, location.origin).searchParams.get('cursor') ?? undefined) : undefined
