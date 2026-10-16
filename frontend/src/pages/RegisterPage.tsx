import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import type { RegisterRequest } from '../api'
import { useAuth } from '../auth/useAuth'
import { ErrorBanner } from '../components/ErrorBanner'
import { Field } from '../components/Field'

const EMPTY_FORM: RegisterRequest = { email: '', password: '', first_name: '', last_name: '' }

export function RegisterPage() {
  const { state, register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState<RegisterRequest>(EMPTY_FORM)
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  if (state.status === 'authenticated') {
    return <Navigate to="/profile" replace />
  }

  function update(field: keyof RegisterRequest) {
    return (event: { target: { value: string } }) => setForm({ ...form, [field]: event.target.value })
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      // Registers, then logs in with the same credentials
      await register(form)
      navigate('/profile', { replace: true })
    } catch (caught) {
      setError(caught)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card narrow">
      <h1>Create an account</h1>
      <form onSubmit={handleSubmit} className="form">
        <div className="field-row">
          <Field label="First name" name="first_name" autoComplete="given-name" required maxLength={100}
            value={form.first_name} onChange={update('first_name')} />
          <Field label="Last name" name="last_name" autoComplete="family-name" required maxLength={100}
            value={form.last_name} onChange={update('last_name')} />
        </div>
        <Field label="Email" name="email" type="email" autoComplete="email" required value={form.email}
          onChange={update('email')} />
        <Field label="Password" name="password" type="password" autoComplete="new-password" required minLength={8}
          hint="At least 8 characters" value={form.password} onChange={update('password')} />
        <ErrorBanner error={error} />
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="muted">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
