import { api } from './client'
import type { Page } from './learning'

export interface Person {
  id: number
  username: string
  name: string
  headline: string
  avatar: string | null
  role: string
}

export interface Suggestion extends Person {
  shared_skills: number
}

export interface Connection {
  id: number
  status: 'pending' | 'accepted'
  direction: 'incoming' | 'outgoing'
  person: Person
  created_at: string
  accepted_at: string | null
}

export interface Relationship {
  following: boolean
  followed_by: boolean
  followers: number
  following_count: number
  connections: number
  connection: Pick<Connection, 'id' | 'status' | 'direction'> | null
}

export interface FollowRow {
  person: Person
  since: string
}

const u = encodeURIComponent

export const network = {
  relationship: (username: string) => api<Relationship>(`/network/${u(username)}/`),
  follow: (username: string) => api<Relationship>(`/network/${u(username)}/follow/`, { method: 'POST' }),
  unfollow: (username: string) => api<Relationship>(`/network/${u(username)}/follow/`, { method: 'DELETE' }),
  followers: (username: string) => api<Page<FollowRow>>(`/network/${u(username)}/followers/`),
  following: (username: string) => api<Page<FollowRow>>(`/network/${u(username)}/following/`),
  suggestions: () => api<Suggestion[]>('/network/suggestions/'),
  connections: (status: 'accepted' | 'incoming' | 'outgoing' = 'accepted') =>
    api<Page<Connection>>(`/connections/?status=${status}`),
  connect: (username: string) => api<Connection>('/connections/', { method: 'POST', body: { username } }),
  accept: (id: number) => api<Connection>(`/connections/${id}/accept/`, { method: 'POST' }),
  decline: (id: number) => api<void>(`/connections/${id}/decline/`, { method: 'POST' }),
  remove: (id: number) => api<void>(`/connections/${id}/`, { method: 'DELETE' }),
}
