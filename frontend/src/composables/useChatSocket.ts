import { onUnmounted, ref, watch, type Ref } from 'vue'
import { getAccessToken } from '@/api/client'
import type { WsClientEvent, WsServerEvent } from '@/types'
import { useChatsStore } from '@/stores/chats'

function wsUrl(chatId: string, token: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const base = import.meta.env.VITE_WS_BASE || `${proto}//${window.location.host}`
  return `${base}/ws/chats/${chatId}/?token=${encodeURIComponent(token)}`
}

export function useChatSocket(chatId: Ref<string | null>) {
  const connected = ref(false)
  const chats = useChatsStore()
  let socket: WebSocket | null = null
  let typingTimer: ReturnType<typeof setTimeout> | null = null

  function disconnect() {
    if (typingTimer) clearTimeout(typingTimer)
    socket?.close()
    socket = null
    connected.value = false
  }

  function connect(id: string) {
    disconnect()
    const token = getAccessToken()
    if (!token) return

    socket = new WebSocket(wsUrl(id, token))
    socket.onopen = () => {
      connected.value = true
    }
    socket.onclose = () => {
      connected.value = false
    }
    socket.onmessage = (ev) => {
      const event = JSON.parse(ev.data) as WsServerEvent
      handleEvent(event)
    }
  }

  function handleEvent(event: WsServerEvent) {
    switch (event.type) {
      case 'message.new':
        chats.upsertMessage(event.payload)
        break
      case 'message.deleted':
        chats.markDeleted(event.payload.chat, event.payload.id)
        break
      case 'typing':
        chats.setTyping(
          event.payload.chat_id,
          event.payload.user_id,
          event.payload.is_typing,
        )
        break
      default:
        break
    }
  }

  function send(event: WsClientEvent) {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(event))
    }
  }

  function sendMessage(content: string) {
    send({ type: 'message.send', payload: { content } })
  }

  function notifyTyping() {
    send({ type: 'typing', payload: { is_typing: true } })
    if (typingTimer) clearTimeout(typingTimer)
    typingTimer = setTimeout(() => {
      send({ type: 'typing', payload: { is_typing: false } })
    }, 1500)
  }

  watch(
    chatId,
    (id) => {
      if (id) connect(id)
      else disconnect()
    },
    { immediate: true },
  )

  onUnmounted(disconnect)

  return { connected, sendMessage, notifyTyping, send }
}
