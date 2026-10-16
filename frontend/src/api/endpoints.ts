import { ApiError, type ApiClient } from './client'
import type {
  DataListResponse,
  DataResponse,
  DataSchema,
  LoginRequest,
  RegisterRequest,
  UserEntity,
  UserLoginResponse,
} from './types'

export interface ListQuery {
  page: number
  pageSize: number
  filters: Record<string, string>
}

export function createApi(client: ApiClient) {
  return {
    hasSession: () => client.tokens.get() !== null,

    register: (body: RegisterRequest) =>
      client.request<UserEntity>('/users/register', { method: 'POST', body }),

    async login(body: LoginRequest): Promise<UserEntity> {
      const response = await client.request<UserLoginResponse>('/users/login', { method: 'POST', body })
      client.tokens.set(response.token)
      return response.user
    },

    async logout(): Promise<void> {
      const refresh = client.tokens.get()?.refresh
      client.tokens.set(null)
      if (!refresh) {
        return
      }
      try {
        await client.request<void>('/users/logout', { method: 'POST', body: { refresh_token: refresh } })
      } catch (error) {
        // Already expired or revoked on the server: the local session is cleared anyway
        if (!(error instanceof ApiError)) {
          throw error
        }
      }
    },

    profile: () => client.request<UserEntity>('/users/profile', { auth: true }),

    describe: (slug: string) =>
      client.request<DataSchema>(`/data/${encodeURIComponent(slug)}/describe`, { auth: true }),

    list(slug: string, { page, pageSize, filters }: ListQuery) {
      const params = new URLSearchParams({ _page: String(page), _pageSize: String(pageSize) })
      for (const [field, value] of Object.entries(filters)) {
        if (value.trim() !== '') {
          params.set(field, value.trim())
        }
      }
      return client.request<DataListResponse>(`/data/${encodeURIComponent(slug)}?${params}`, { auth: true })
    },

    retrieve: (slug: string, id: string) =>
      client.request<DataResponse>(`/data/${encodeURIComponent(slug)}/${encodeURIComponent(id)}`, {
        auth: true,
      }),
  }
}

export type Api = ReturnType<typeof createApi>
