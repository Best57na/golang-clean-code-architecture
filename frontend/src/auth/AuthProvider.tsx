import { useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, apiClient } from '../api'
import { AuthContext, type AuthState, type AuthValue } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  // With stored tokens we don't know yet whether they are still valid
  const [state, setState] = useState<AuthState>(() =>
    api.hasSession() ? { status: 'loading' } : { status: 'anonymous' },
  )

  useEffect(() => {
    apiClient.onSessionExpired(() => setState({ status: 'anonymous' }))
    return () => apiClient.onSessionExpired(null)
  }, [])

  useEffect(() => {
    if (!api.hasSession()) {
      return
    }
    let active = true
    api
      .profile()
      .then((user) => active && setState({ status: 'authenticated', user }))
      .catch(() => active && setState({ status: 'anonymous' }))
    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthValue>(
    () => ({
      state,
      async login(body) {
        const user = await api.login(body)
        setState({ status: 'authenticated', user })
      },
      async register(body) {
        await api.register(body)
        const user = await api.login({ email: body.email, password: body.password })
        setState({ status: 'authenticated', user })
      },
      async logout() {
        await api.logout()
        setState({ status: 'anonymous' })
      },
    }),
    [state],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
