import type { InputHTMLAttributes } from 'react'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  hint?: string
}

export function Field({ label, hint, id, ...input }: FieldProps) {
  const inputId = id ?? input.name
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} {...input} />
      {hint && <small className="muted">{hint}</small>}
    </div>
  )
}
