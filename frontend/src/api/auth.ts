import { api, setTokens, clearTokens } from './client'
import type { BannerStyle, User } from '@/types'

export type { BannerStyle } from '@/types'

export async function register(username: string, password: string, email = '') {
  const data = await api<{ user: User; access: string; refresh: string }>(
    '/api/auth/register/',
    { method: 'POST', body: JSON.stringify({ username, password, email }) },
  )
  setTokens(data.access, data.refresh)
  return data.user
}

export async function login(username: string, password: string) {
  const tokens = await api<{ access: string; refresh: string }>(
    '/api/auth/token/',
    { method: 'POST', body: JSON.stringify({ username, password }) },
  )
  setTokens(tokens.access, tokens.refresh)
  return fetchMe()
}

export async function fetchMe() {
  return api<User>('/api/users/me/')
}

export type ProfileUpdate = {
  username?: string
  first_name?: string
  last_name?: string
  phone?: string
  bio?: string
  banner_style?: BannerStyle | null
  avatar?: File | null
  banner_image?: File | null
}

export async function updateMe(patch: ProfileUpdate): Promise<User> {
  const hasFile = patch.avatar instanceof File || patch.banner_image instanceof File
  if (hasFile) {
    const form = new FormData()
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined) continue
      if (value === null) {
        form.append(key, '')
        continue
      }
      if (key === 'banner_style') {
        form.append(key, JSON.stringify(value))
        continue
      }
      if (value instanceof File) {
        form.append(key, value)
        continue
      }
      form.append(key, String(value))
    }
    return api<User>('/api/users/me/', { method: 'PATCH', body: form })
  }

  const body: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(patch)) {
    if (value !== undefined) body[key] = value
  }
  return api<User>('/api/users/me/', {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function logout() {
  try {
    await api('/api/auth/logout/', { method: 'POST' })
  } finally {
    clearTokens()
  }
}
