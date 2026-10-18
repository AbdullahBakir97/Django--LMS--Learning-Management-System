import { api } from './client'

export type Role = 'learner' | 'instructor' | 'admin'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: Role
  date_joined: string
}

export interface LoginResponse {
  access: string
  user: User
}

export const auth = {
  login: (email: string, password: string) =>
    api<LoginResponse>('/auth/login/', { method: 'POST', body: { email, password } }),
  logout: () => api('/auth/logout/', { method: 'POST' }),
  register: (data: { username: string; email: string; password1: string; password2: string }) =>
    api<{ detail: string }>('/auth/register/', { method: 'POST', body: data }),
  verifyEmail: (key: string) => api('/auth/verify-email/', { method: 'POST', body: { key } }),
  resendEmail: (email: string) => api('/auth/resend-email/', { method: 'POST', body: { email } }),
  me: () => api<User>('/auth/user/'),
  updateMe: (data: Partial<Pick<User, 'first_name' | 'last_name'>>) =>
    api<User>('/auth/user/', { method: 'PATCH', body: data }),
  requestPasswordReset: (email: string) => api('/auth/password/reset/', { method: 'POST', body: { email } }),
  confirmPasswordReset: (data: {
    uid: string
    token: string
    new_password1: string
    new_password2: string
  }) => api('/auth/password/reset/confirm/', { method: 'POST', body: data }),
}
