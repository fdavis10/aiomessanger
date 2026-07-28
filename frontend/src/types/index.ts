export interface BannerStyle {
  from: string
  to: string
  motifs: string[]
}

export interface User {
  id: number
  username: string
  email?: string
  first_name?: string
  last_name?: string
  avatar?: string | null
  banner_image?: string | null
  banner_style?: BannerStyle | null
  phone?: string
  bio?: string
  last_seen_at?: string | null
  date_joined?: string
}

export interface ChatMember {
  id: number
  user: User
  role: 'owner' | 'admin' | 'member'
  joined_at: string
  last_read_at: string | null
}

export interface Chat {
  id: string
  type: 'private' | 'group'
  title: string
  avatar: string | null
  created_at: string
  updated_at: string
  members: ChatMember[]
}

export interface AttachmentMeta {
  id: string
  mime_type: string
  size_bytes: number
  original_filename: string
  created_at: string
}

export interface Message {
  id: string
  chat: string
  sender: User | null
  content: string | null
  content_type: string
  attachment?: AttachmentMeta | null
  created_at: string
  edited_at: string | null
  is_deleted: boolean
}

export interface Paginated<T> {
  next: string | null
  previous: string | null
  results: T[]
}

export type WsClientEvent =
  | { type: 'message.send'; payload: { content: string } }
  | { type: 'message.delete'; payload: { message_id: string } }
  | { type: 'typing'; payload: { is_typing: boolean } }
  | { type: 'read.receipt'; payload: { message_id: string } }

export type WsServerEvent =
  | { type: 'message.new'; payload: Message }
  | { type: 'message.deleted'; payload: { id: string; chat: string; is_deleted: boolean } }
  | { type: 'message.ack'; payload: Message | { id: string; chat: string; is_deleted: boolean } }
  | { type: 'typing'; payload: { chat_id: string; user_id: number; is_typing: boolean } }
  | { type: 'presence.online'; payload: { user_id: number; chat_id: string } }
  | { type: 'presence.offline'; payload: { user_id: number; chat_id: string } }
  | { type: 'read.receipt'; payload: { chat_id: string; message_id: string; user_id: number } }
  | { type: 'error'; payload: { detail: string } }
