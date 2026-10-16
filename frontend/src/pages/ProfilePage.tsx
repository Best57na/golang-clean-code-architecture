import { useAuth } from '../auth/useAuth'

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function ProfilePage() {
  const { state } = useAuth()
  if (state.status !== 'authenticated') {
    return null
  }
  const { user } = state

  return (
    <section className="card narrow">
      <div className="profile-head">
        <span className="avatar" aria-hidden="true">
          {user.first_name.charAt(0).toUpperCase()}
          {user.last_name.charAt(0).toUpperCase()}
        </span>
        <div>
          <h1>
            {user.first_name} {user.last_name}
          </h1>
          <p className="muted">{user.email}</p>
        </div>
      </div>
      <dl className="details">
        <dt>User ID</dt>
        <dd>{user.id}</dd>
        <dt>Created</dt>
        <dd>{dateFormat.format(new Date(user.created_at))}</dd>
        <dt>Updated</dt>
        <dd>{dateFormat.format(new Date(user.updated_at))}</dd>
      </dl>
      <p className="muted small">
        Loaded from <code>GET /api/v1/users/profile</code>. The access token is refreshed automatically when it
        expires.
      </p>
    </section>
  )
}
