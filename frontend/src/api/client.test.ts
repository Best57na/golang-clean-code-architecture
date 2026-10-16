import { describe, expect, it, vi } from 'vitest'

import { ApiError, createApiClient, type TokenStorage } from './client'
import { createApi } from './endpoints'
import type { TokenPair } from './types'

function memoryStorage(initial: TokenPair | null = null): TokenStorage & { value: TokenPair | null } {
  return {
    value: initial,
    get() {
      return this.value
    },
    set(tokens) {
      this.value = tokens
    },
  }
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const user = {
  id: 1,
  email: 'a@b.co',
  first_name: 'A',
  last_name: 'B',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('api client', () => {
  it('sends the access token on authenticated requests', async () => {
    const fetch = vi.fn(async () => json(200, user))
    const client = createApiClient({ baseUrl: '/api', tokens: memoryStorage({ access: 'A1', refresh: 'R1' }), fetch })

    await client.request('/users/profile', { auth: true })

    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/api/users/profile')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer A1')
  })

  it('refreshes once on 401, stores new tokens and retries', async () => {
    const tokens = memoryStorage({ access: 'old', refresh: 'R1' })
    const fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/refresh-token')) {
        return json(200, { user, token: { access: 'new', refresh: 'R2' } })
      }
      const auth = new Headers(init?.headers).get('Authorization')
      return auth === 'Bearer new' ? json(200, user) : json(401, { trace_id: 'middleware-002', message: 'expired' })
    })
    const client = createApiClient({ baseUrl: '', tokens, fetch })

    await expect(client.request('/users/profile', { auth: true })).resolves.toEqual(user)
    expect(tokens.value).toEqual({ access: 'new', refresh: 'R2' })
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it('shares one refresh between parallel 401 responses', async () => {
    const tokens = memoryStorage({ access: 'old', refresh: 'R1' })
    const fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).endsWith('/refresh-token')) {
        return json(200, { user, token: { access: 'new', refresh: 'R2' } })
      }
      const auth = new Headers(init?.headers).get('Authorization')
      return auth === 'Bearer new' ? json(200, user) : json(401, {})
    })
    const client = createApiClient({ baseUrl: '', tokens, fetch })

    await Promise.all([
      client.request('/users/profile', { auth: true }),
      client.request('/users/profile', { auth: true }),
    ])

    const refreshCalls = fetch.mock.calls.filter(([url]) => String(url).endsWith('/refresh-token'))
    expect(refreshCalls).toHaveLength(1)
  })

  it('clears the session and notifies when refresh fails', async () => {
    const tokens = memoryStorage({ access: 'old', refresh: 'revoked' })
    const fetch = vi.fn(async () => json(401, { trace_id: 'users-003', message: 'user token not found' }))
    const client = createApiClient({ baseUrl: '', tokens, fetch })
    const expired = vi.fn()
    client.onSessionExpired(expired)

    await expect(client.request('/users/profile', { auth: true })).rejects.toBeInstanceOf(ApiError)
    expect(tokens.value).toBeNull()
    expect(expired).toHaveBeenCalledOnce()
  })

  it('turns error bodies into ApiError with trace id', async () => {
    const fetch = vi.fn(async () => json(409, { trace_id: 'users-001', message: 'email has been used' }))
    const client = createApiClient({ baseUrl: '', tokens: memoryStorage(), fetch })

    const error = await client.request('/users/register', { method: 'POST', body: {} }).catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 409, traceId: 'users-001', message: 'email has been used' })
  })

  it('handles non-JSON error pages', async () => {
    const fetch = vi.fn(async () => new Response('<html>Bad Gateway</html>', { status: 502, statusText: 'Bad Gateway' }))
    const client = createApiClient({ baseUrl: '', tokens: memoryStorage(), fetch })

    await expect(client.request('/')).rejects.toMatchObject({ status: 502, traceId: 'http-502' })
  })

  it('returns undefined for 204 No Content', async () => {
    const fetch = vi.fn(async () => new Response(null, { status: 204 }))
    const client = createApiClient({ baseUrl: '', tokens: memoryStorage(), fetch })

    await expect(client.request('/users/logout', { method: 'POST', body: {} })).resolves.toBeUndefined()
  })
})

describe('api endpoints', () => {
  it('login stores tokens and logout clears them even if the server rejects', async () => {
    const tokens = memoryStorage()
    const fetch = vi.fn(async (url: RequestInfo | URL) =>
      String(url).endsWith('/login')
        ? json(200, { user, token: { access: 'A', refresh: 'R' } })
        : json(401, { trace_id: 'users-004', message: 'user token not found' }),
    )
    const api = createApi(createApiClient({ baseUrl: '', tokens, fetch }))

    await expect(api.login({ email: user.email, password: 'x' })).resolves.toEqual(user)
    expect(tokens.value).toEqual({ access: 'A', refresh: 'R' })

    await api.logout()
    expect(tokens.value).toBeNull()
  })

  it('list sends paging and non-empty filters as query params', async () => {
    const fetch = vi.fn(async () => json(200, { data: [] }))
    const api = createApi(createApiClient({ baseUrl: '', tokens: memoryStorage({ access: 'A', refresh: 'R' }), fetch }))

    await api.list('users', { page: 2, pageSize: 5, filters: { email: ' a@b.co ', first_name: '' } })

    const [url] = fetch.mock.calls[0] as unknown as [string]
    expect(url).toBe('/data/users?_page=2&_pageSize=5&email=a%40b.co')
  })
})
