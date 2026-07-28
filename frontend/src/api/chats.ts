import { api, getAccessToken } from './client'
import type { Chat, Message, Paginated, User } from '@/types'

export function listChats() {
  return api<Paginated<Chat>>('/api/chats/')
}

export function createPrivateChat(userId: number) {
  return api<Chat>('/api/chats/', {
    method: 'POST',
    body: JSON.stringify({ type: 'private', user_id: userId }),
  })
}

export function createGroupChat(title: string, memberIds: number[]) {
  return api<Chat>('/api/chats/', {
    method: 'POST',
    body: JSON.stringify({ type: 'group', title, member_ids: memberIds }),
  })
}

export function getChat(chatId: string) {
  return api<Chat>(`/api/chats/${chatId}/`)
}

export function listMessages(chatId: string, cursor?: string | null) {
  const qs = cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''
  return api<Paginated<Message>>(`/api/chats/${chatId}/messages/${qs}`)
}

export function sendMessage(chatId: string, content: string) {
  return api<Message>(`/api/chats/${chatId}/messages/`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}

export async function uploadAttachment(
  chatId: string,
  file: File,
  caption = '',
): Promise<Message> {
  const form = new FormData()
  form.append('file', file)
  if (caption) form.append('caption', caption)
  const token = getAccessToken()
  const headers: HeadersInit = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`/api/chats/${chatId}/attachments/`, {
    method: 'POST',
    headers,
    body: form,
    credentials: 'include',
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || `Upload failed (${res.status})`)
  }
  return res.json()
}

export function attachmentDownloadUrl(attachmentId: string): string {
  return `/api/attachments/${attachmentId}/download/`
}

export function getUser(userId: number) {
  return api<User>(`/api/users/${userId}/`)
}
