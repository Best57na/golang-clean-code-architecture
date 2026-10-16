import { useEffect, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api, ApiError, type DataListResponse, type DataResponse, type DataSchema, type SchemaField } from '../api'
import { useAuth } from '../auth/useAuth'
import { ErrorBanner } from '../components/ErrorBanner'

// The API has no endpoint that lists models; keep in sync with app/config/crud_models.py
const MODELS = ['users', 'user-permissions']
const PAGE_SIZES = [10, 25, 50]
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function DataPage() {
  const [params, setParams] = useSearchParams()
  const slug = params.get('model') ?? MODELS[0]

  return (
    <section className="card">
      <div className="data-header">
        <h1>Data browser</h1>
        <label className="inline-field">
          <span>Model</span>
          <select value={slug} onChange={(event) => setParams({ model: event.target.value })}>
            {MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
      </div>
      {/* key resets paging, filters and detail when the model changes */}
      <DataBrowser key={slug} slug={slug} />
    </section>
  )
}

function DataBrowser({ slug }: { slug: string }) {
  const [schema, setSchema] = useState<DataSchema | null>(null)
  const [result, setResult] = useState<DataListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0])
  const [draftFilters, setDraftFilters] = useState<Record<string, string>>({})
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [detail, setDetail] = useState<DataResponse | null>(null)
  const [error, setError] = useState<unknown>(null)
  // Loading = the last finished query is not the current one (derived, not stored)
  const queryKey = JSON.stringify([page, pageSize, filters])
  const [finishedKey, setFinishedKey] = useState<string | null>(null)
  const loading = finishedKey !== queryKey

  useEffect(() => {
    let active = true
    api
      .describe(slug)
      .then((loaded) => active && setSchema(loaded))
      .catch((caught) => active && setError(caught))
    return () => {
      active = false
    }
  }, [slug])

  useEffect(() => {
    let active = true
    const key = JSON.stringify([page, pageSize, filters])
    api
      .list(slug, { page, pageSize, filters })
      .then((loaded) => {
        if (active) {
          setResult(loaded)
          setError(null)
        }
      })
      .catch((caught) => active && setError(caught))
      .finally(() => active && setFinishedKey(key))
    return () => {
      active = false
    }
  }, [slug, page, pageSize, filters])

  function applyFilters(event: FormEvent) {
    event.preventDefault()
    setPage(1)
    setFilters(draftFilters)
  }

  function clearFilters() {
    setDraftFilters({})
    setPage(1)
    setFilters({})
  }

  async function showDetail(id: unknown) {
    try {
      setDetail(await api.retrieve(slug, String(id)))
    } catch (caught) {
      setError(caught)
    }
  }

  if (error instanceof ApiError && error.status === 403) {
    return <AccessDenied />
  }

  const fields = schema?.fields ?? result?.data_schema.fields ?? []

  return (
    <>
      {schema && (
        <form className="filters" onSubmit={applyFilters} aria-label="Filters">
          {schema.fields.map((field) => (
            <FilterInput
              key={field.name}
              field={field}
              value={draftFilters[field.name] ?? ''}
              onChange={(value) => setDraftFilters({ ...draftFilters, [field.name]: value })}
            />
          ))}
          <div className="filter-actions">
            <button type="submit" className="button primary">
              Apply
            </button>
            <button type="button" className="button" onClick={clearFilters}>
              Clear
            </button>
          </div>
        </form>
      )}

      <ErrorBanner error={error} />

      <div className="table-wrap" aria-busy={loading}>
        <table>
          <thead>
            <tr>
              {fields.map((field) => (
                <th key={field.name} scope="col">
                  {field.name}
                  <span className="type">{field.type}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result?.data.map((row) => (
              <tr key={String(row.id)} onClick={() => showDetail(row.id)} className="clickable">
                {fields.map((field) => (
                  <td key={field.name}>{formatValue(row[field.name], field.type)}</td>
                ))}
              </tr>
            ))}
            {result && result.data.length === 0 && (
              <tr>
                <td colSpan={fields.length || 1} className="muted empty">
                  No rows match.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {result && (
        <div className="pagination">
          <span className="muted">
            {result.total_data} {result.total_data === 1 ? 'row' : 'rows'} · page {result.page} of{' '}
            {Math.max(result.total_page, 1)}
          </span>
          <div className="pagination-controls">
            <label className="inline-field">
              <span>Rows</span>
              <select
                value={pageSize}
                onChange={(event) => {
                  setPage(1)
                  setPageSize(Number(event.target.value))
                }}
              >
                {PAGE_SIZES.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <button
              type="button"
              className="button"
              disabled={page >= result.total_page}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {detail && (
        <aside className="detail" aria-label="Row detail">
          <div className="detail-head">
            <h2>
              {slug} #{String(detail.data.id)}
            </h2>
            <button type="button" className="link-button" onClick={() => setDetail(null)}>
              Close
            </button>
          </div>
          <pre>{JSON.stringify(detail.data, null, 2)}</pre>
        </aside>
      )}
    </>
  )
}

function FilterInput({
  field,
  value,
  onChange,
}: {
  field: SchemaField
  value: string
  onChange: (value: string) => void
}) {
  const id = `filter-${field.name}`
  return (
    <div className="field">
      <label htmlFor={id}>{field.name}</label>
      {field.type === 'boolean' ? (
        <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">any</option>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      ) : (
        <input
          id={id}
          type={field.type === 'int' ? 'number' : 'text'}
          placeholder={field.type === 'datetime' ? 'ISO 8601' : 'exact match'}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </div>
  )
}

function AccessDenied() {
  const { state } = useAuth()
  const userId = state.status === 'authenticated' ? state.user.id : '<user id>'
  const sql = `INSERT INTO user_permissions (user_id, permission, updated_at) VALUES (${userId}, 'admin', now());`
  return (
    <div className="banner warning" role="alert">
      <p>
        <strong>This account does not have the admin permission.</strong> The data API exposes every registered
        table, so only admins can use it.
      </p>
      <p>To grant it with Docker Compose:</p>
      <pre>{`docker compose exec db psql -U postgres -c "${sql}"`}</pre>
    </div>
  )
}

function formatValue(value: unknown, type: string): string {
  if (value === null || value === undefined) {
    return '—'
  }
  if (type === 'datetime' && typeof value === 'string') {
    return dateFormat.format(new Date(value))
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}
