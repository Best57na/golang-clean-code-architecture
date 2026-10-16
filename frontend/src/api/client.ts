import type { TokenPair, UserLoginResponse } from './types'

/** Error returned by the API: {"trace_id": "...", "message": "..."}. */
export class ApiError extends Error {
  readonly status: number
  readonly traceId: string

  constructor(status: number, traceId: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.traceId = traceId
  }
}

export interface TokenStorage {
  get(): TokenPair | null
  set(tokens: TokenPair | null): void
}

const STORAGE_KEY = 'auth.tokens'

/**
 * Keeps tokens in localStorage so a reload stays signed in.
 * Trade-off: readable by scripts on the page. An httpOnly cookie would need backend changes.
 */
export const localTokenStorage: TokenStorage = {
  get() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? (JSON.parse(raw) as TokenPair) : null
    } catch {
      return null
    }
  },
  set(tokens) {
    try {
      if (tokens) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch {
      // Storage unavailable (private mode); the session just won't survive a reload
    }
  },
}

export interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  /** Send the access token and refresh it once if the API answers 401. */
  auth?: boolean
}

export interface ApiClientOptions {
  baseUrl: string
  tokens: TokenStorage
  fetch?: typeof fetch
}

export type ApiClient = ReturnType<typeof createApiClient>

export function createApiClient({ baseUrl, tokens, fetch: fetchImpl = fetch }: ApiClientOptions) {
  // Shared so parallel requests that all get 401 trigger only one refresh
  let refreshing: Promise<boolean> | null = null
  let sessionExpiredListener: (() => void) | null = null

  function send(path: string, init: RequestInit, auth: boolean): Promise<Response> {
    const headers = new Headers(init.headers)
    if (init.body !== undefined) {
      headers.set('Content-Type', 'application/json')
    }
    const access = tokens.get()?.access
    if (auth && access) {
      headers.set('Authorization', `Bearer ${access}`)
    }
    return fetchImpl(baseUrl + path, { ...init, headers })
  }

  async function refreshTokens(): Promise<boolean> {
    const refresh = tokens.get()?.refresh
    if (!refresh) {
      return false
    }
    refreshing ??= (async () => {
      try {
        const response = await send(
          '/users/refresh-token',
          { method: 'POST', body: JSON.stringify({ refresh_token: refresh }) },
          false,
        )
        if (!response.ok) {
          return false
        }
        const body = (await response.json()) as UserLoginResponse
        tokens.set(body.token)
        return true
      } finally {
        refreshing = null
      }
    })()
    return refreshing
  }

  async function request<T>(path: string, { method = 'GET', body, auth = false }: RequestOptions = {}): Promise<T> {
    const init: RequestInit = { method, body: body === undefined ? undefined : JSON.stringify(body) }

    let response = await send(path, init, auth)
    if (auth && response.status === 401) {
      if (await refreshTokens()) {
        response = await send(path, init, auth)
      }
      if (response.status === 401) {
        tokens.set(null)
        sessionExpiredListener?.()
      }
    }
    return parseResponse<T>(response)
  }

  return {
    request,
    tokens,
    onSessionExpired(listener: (() => void) | null) {
      sessionExpiredListener = listener
    },
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T
  }
  const text = await response.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : undefined
  } catch {
    // Not JSON, e.g. an HTML error page from a proxy
    data = undefined
  }
  if (!response.ok) {
    const error = (data ?? {}) as Partial<{ trace_id: string; message: string }>
    throw new ApiError(
      response.status,
      error.trace_id ?? `http-${response.status}`,
      error.message ?? (response.statusText || 'request failed'),
    )
  }
  return data as T
}
