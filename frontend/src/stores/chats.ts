import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as chatsApi from '@/api/chats'
import type { Chat, Message } from '@/types'
import { useAuthStore } from './auth'
import { useLocaleStore } from './locale'

export const useChatsStore = defineStore('chats', () => {
  const chats = ref<Chat[]>([])
  const activeChatId = ref<string | null>(null)
  const messagesByChat = ref<Record<string, Message[]>>({})
  const typingUsers = ref<Record<string, number[]>>({})
  const loadingChats = ref(false)
  const loadingMessages = ref(false)
  const error = ref<string | null>(null)

  const activeChat = computed(
    () => chats.value.find((c) => c.id === activeChatId.value) ?? null,
  )

  const activeMessages = computed(() => {
    if (!activeChatId.value) return []
    return messagesByChat.value[activeChatId.value] ?? []
  })

  function chatTitle(chat: Chat): string {
    const locale = useLocaleStore()
    if (chat.type === 'group') return chat.title || locale.t('group')
    const auth = useAuthStore()
    const other = chat.members.find((m) => m.user.id !== auth.user?.id)
    return other?.user.username ?? locale.t('privateChat')
  }

  async function loadChats() {
    loadingChats.value = true
    error.value = null
    try {
      const page = await chatsApi.listChats()
      chats.value = page.results
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load chats'
    } finally {
      loadingChats.value = false
    }
  }

  async function selectChat(chatId: string) {
    activeChatId.value = chatId
    if (!messagesByChat.value[chatId]) {
      await loadMessages(chatId)
    }
  }

  async function loadMessages(chatId: string) {
    loadingMessages.value = true
    try {
      const page = await chatsApi.listMessages(chatId)
      // API returns newest-first; reverse for chronological UI.
      messagesByChat.value[chatId] = [...page.results].reverse()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load messages'
    } finally {
      loadingMessages.value = false
    }
  }

  async function createPrivate(userId: number) {
    const chat = await chatsApi.createPrivateChat(userId)
    if (!chats.value.find((c) => c.id === chat.id)) {
      chats.value.unshift(chat)
    }
    await selectChat(chat.id)
    return chat
  }

  function upsertMessage(message: Message) {
    const list = messagesByChat.value[message.chat] ?? []
    if (list.some((m) => m.id === message.id)) return
    messagesByChat.value[message.chat] = [...list, message]
    const chat = chats.value.find((c) => c.id === message.chat)
    if (chat) {
      chat.updated_at = message.created_at
      chats.value = [
        chat,
        ...chats.value.filter((c) => c.id !== chat.id),
      ]
    }
  }

  function markDeleted(chatId: string, messageId: string) {
    const list = messagesByChat.value[chatId]
    if (!list) return
    messagesByChat.value[chatId] = list.map((m) =>
      m.id === messageId ? { ...m, content: null, is_deleted: true } : m,
    )
  }

  function setTyping(chatId: string, userId: number, isTyping: boolean) {
    const auth = useAuthStore()
    if (userId === auth.user?.id) return
    const current = new Set(typingUsers.value[chatId] ?? [])
    if (isTyping) current.add(userId)
    else current.delete(userId)
    typingUsers.value = {
      ...typingUsers.value,
      [chatId]: [...current],
    }
  }

  return {
    chats,
    activeChatId,
    activeChat,
    activeMessages,
    messagesByChat,
    typingUsers,
    loadingChats,
    loadingMessages,
    error,
    chatTitle,
    loadChats,
    selectChat,
    loadMessages,
    createPrivate,
    upsertMessage,
    markDeleted,
    setTyping,
  }
})
