import { createApiClient, localTokenStorage } from './client'
import { createApi } from './endpoints'

export { ApiError } from './client'
export type * from './types'

export const apiClient = createApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  tokens: localTokenStorage,
})

export const api = createApi(apiClient)
