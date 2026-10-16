import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './useAuth'

/** Renders child routes only for signed-in users; others go to /login and come back after. */
export function RequireAuth() {
  const { state } = useAuth()
  const location = useLocation()

  if (state.status === 'loading') {
    return <p className="muted">Checking session…</p>
  }
  if (state.status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}
