import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, refreshAccessToken, setAccessToken } from '@/api/client'

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    setAccessToken(null)
  })

  it('sends the bearer token and parses JSON', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(200, { ok: true }))
    setAccessToken('abc')
    await expect(api('/auth/user/')).resolves.toEqual({ ok: true })
    const headers = (fetchMock.mock.calls[0]![1] as RequestInit).headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer abc')
  })

  it('refreshes once on 401 and retries with the new token', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(json(401, { status: 401, title: 'Unauthorized', type: 'about:blank' }))
      .mockResolvedValueOnce(json(200, { access: 'fresh' }))
      .mockResolvedValueOnce(json(200, { id: 1 }))
    await expect(api('/auth/user/')).resolves.toEqual({ id: 1 })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    const retryHeaders = (fetchMock.mock.calls[2]![1] as RequestInit).headers as Record<string, string>
    expect(retryHeaders.Authorization).toBe('Bearer fresh')
  })

  it('surfaces problem documents as ApiError with field access', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json(400, { type: 'about:blank', title: 'Bad Request', status: 400, errors: { email: ['Taken.'] } }),
    )
    const error = (await api('/auth/register/', { method: 'POST', body: {} }).catch(
      (e: unknown) => e,
    )) as ApiError
    expect(error).toBeInstanceOf(ApiError)
    expect(error.field('email')).toBe('Taken.')
  })

  it('reads a bare list of errors as the general message', () => {
    const error = new ApiError({
      type: 'about:blank',
      title: 'Bad Request',
      status: 400,
      errors: ['You are already enrolled.'],
    })
    expect(error.nonField).toBe('You are already enrolled.')
    expect(error.field('email')).toBeUndefined()
  })

  it('returns null when the refresh cookie is missing', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(401, {}))
    await expect(refreshAccessToken()).resolves.toBeNull()
  })
})
