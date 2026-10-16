import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ErrorBanner } from '../components/ErrorBanner'
import { Field } from '../components/Field'

export function LoginPage() {
  const { state, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/profile'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  if (state.status === 'authenticated') {
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (caught) {
      setError(caught)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card narrow">
      <h1>Log in</h1>
      <form onSubmit={handleSubmit} className="form">
        <Field label="Email" name="email" type="email" autoComplete="email" required value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <Field label="Password" name="password" type="password" autoComplete="current-password" required
          value={password} onChange={(e) => setPassword(e.target.value)} />
        <ErrorBanner error={error} />
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="muted">
        No account yet? <Link to="/register">Register</Link>
      </p>
    </section>
  )
}
