import { api } from './client'

export const SEARCH_KINDS = ['people', 'courses', 'groups', 'events', 'jobs', 'companies'] as const
export type SearchKind = (typeof SEARCH_KINDS)[number]

export interface Hit {
  kind: SearchKind
  id: number
  title: string
  subtitle: string
  url: string
  image: string | null
}

export type SearchResults = Partial<Record<SearchKind, Hit[]>>

export const search = (q: string, type?: SearchKind) => {
  const params = new URLSearchParams({ q })
  if (type) params.set('type', type)
  return api<SearchResults>(`/search/?${params}`)
}
