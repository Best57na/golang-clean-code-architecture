import { ApiError } from '../api'

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) {
    return null
  }
  const isApiError = error instanceof ApiError
  return (
    <div className="banner error" role="alert">
      <span>{isApiError ? error.message : 'Cannot reach the API. Is the backend running?'}</span>
      {isApiError && <code className="trace">{error.traceId}</code>}
    </div>
  )
}
