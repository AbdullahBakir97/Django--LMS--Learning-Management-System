/** Thin fetch wrapper: JSON in and out, bearer access token, one silent refresh on 401,
 *  RFC 9457 problem documents surfaced as ApiError. */

export interface Problem {
  type: string
  title: string
  status: number
  detail?: string
  errors?: Record<string, string[] | string> | string[]
}

export class ApiError extends Error {
  constructor(public problem: Problem) {
    super(problem.detail ?? problem.title)
  }
  /** First message for a field, or the general detail. */
  field(name: string): string | undefined {
    const errors = this.problem.errors
    const value = Array.isArray(errors) ? undefined : errors?.[name]
    return Array.isArray(value) ? value[0] : value
  }
  get nonField(): string | undefined {
    // A service's ValidationError("…") arrives as a bare list.
    const errors = this.problem.errors
    const value = Array.isArray(errors) ? errors : errors?.non_field_errors
    return (Array.isArray(value) ? value[0] : value) ?? this.problem.detail
  }
}

const BASE = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '')

let accessToken: string | null = null
let refreshing: Promise<string | null> | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export async function refreshAccessToken(): Promise<string | null> {
  refreshing ??= fetch(`${BASE}/auth/token/refresh/`, { method: 'POST', credentials: 'include' })
    .then(async (r) => (r.ok ? ((await r.json()).access as string) : null))
    .catch(() => null)
    .finally(() => {
      refreshing = null
    })
  const token = await refreshing
  accessToken = token
  return token
}

interface Options {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  retry?: boolean
}

export async function api<T = unknown>(
  path: string,
  { method = 'GET', body, retry = true }: Options = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined && !(body instanceof FormData)) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
  })

  if (response.status === 401 && retry && (await refreshAccessToken())) {
    return api<T>(path, { method, body, retry: false })
  }
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(
      'status' in data
        ? (data as Problem)
        : { type: 'about:blank', title: response.statusText, status: response.status },
    )
  }
  return data as T
}

/** A protected file (a résumé) as a Blob. `url` is the server path the API returned. */
export async function apiBlob(url: string, retry = true): Promise<Blob> {
  const absolute = new URL(url, BASE.startsWith('http') ? BASE : location.origin).toString()
  const response = await fetch(absolute, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    credentials: 'include',
  })
  if (response.status === 401 && retry && (await refreshAccessToken())) return apiBlob(url, false)
  if (!response.ok) {
    throw new ApiError({ type: 'about:blank', title: response.statusText, status: response.status })
  }
  return response.blob()
}
