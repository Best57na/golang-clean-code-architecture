// Mirrors the Pydantic models in app/domain/entities on the backend.

export interface UserEntity {
  id: number
  email: string
  first_name: string
  last_name: string
  created_at: string
  updated_at: string
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface UserLoginResponse {
  user: UserEntity
  token: TokenPair
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface SchemaField {
  name: string
  type: string
}

export interface DataSchema {
  type: 'record'
  name: string
  fields: SchemaField[]
}

export type DataRow = Record<string, unknown>

export interface DataResponse {
  data: DataRow
  data_schema: DataSchema
}

export interface DataListResponse {
  data: DataRow[]
  page: number
  page_size: number
  total_page: number
  total_data: number
  data_schema: DataSchema
}
