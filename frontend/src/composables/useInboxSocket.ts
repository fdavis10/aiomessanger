import { onUnmounted, watch, type Ref } from 'vue'
import { getAccessToken } from '@/api/client'
import type { WsServerEvent } from '@/types'
import { useChatsStore } from '@/stores/chats'
import { useNotificationStore } from '@/stores/notifications'

function inboxUrl(token: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const base = import.meta.env.VITE_WS_BASE || `${proto}//${window.location.host}`
  return `${base}/ws/inbox/?token=${encodeURIComponent(token)}`
}

/** Keep a user-wide socket so toasts work even when no chat is open. */
export function useInboxSocket(enabled: Ref<boolean>, membershipKey: Ref<string>) {
  const chats = useChatsStore()
  const notifications = useNotificationStore()
  let socket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    socket?.close()
    socket = null
  }

  function connect() {
    disconnect()
    const token = getAccessToken()
    if (!token || !enabled.value) return

    socket = new WebSocket(inboxUrl(token))
    socket.onmessage = (ev) => {
      let event: WsServerEvent
      try {
        event = JSON.parse(ev.data) as WsServerEvent
      } catch {
        return
      }
      if (event.type === 'message.new') {
        chats.upsertMessage(event.payload)
        notifications.notifyFromMessage(event.payload)
      } else if (event.type === 'message.deleted') {
        chats.markDeleted(event.payload.chat, event.payload.id)
      }
    }
    socket.onclose = () => {
      socket = null
      if (!enabled.value) return
      reconnectTimer = setTimeout(connect, 2500)
    }
  }

  watch(
    [enabled, membershipKey],
    () => {
      if (enabled.value) connect()
      else disconnect()
    },
    { immediate: true },
  )

  onUnmounted(disconnect)
}
