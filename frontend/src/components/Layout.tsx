import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function Layout() {
  const { state, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark" aria-hidden="true" />
            Clean Architecture Console
          </NavLink>
          <nav aria-label="Main">
            {state.status === 'authenticated' ? (
              <>
                <NavLink to="/profile">Profile</NavLink>
                <NavLink to="/data">Data</NavLink>
                <button type="button" className="link-button" onClick={handleLogout}>
                  Log out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login">Log in</NavLink>
                <NavLink to="/register">Register</NavLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </>
  )
}
