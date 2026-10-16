import { createContext } from 'react'

import type { LoginRequest, RegisterRequest, UserEntity } from '../api'

export type AuthState =
  | { status: 'loading' }
  | { status: 'anonymous' }
  | { status: 'authenticated'; user: UserEntity }

export interface AuthValue {
  state: AuthState
  login(body: LoginRequest): Promise<void>
  register(body: RegisterRequest): Promise<void>
  logout(): Promise<void>
}

export const AuthContext = createContext<AuthValue | null>(null)
