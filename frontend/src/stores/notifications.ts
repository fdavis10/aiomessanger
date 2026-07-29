import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'
import type { Chat, Message } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { useChatsStore } from '@/stores/chats'
import { useLocaleStore } from '@/stores/locale'
import { mediaUrl } from '@/utils/mediaUrl'
import { playNotifySound } from '@/utils/notifySound'

const STORAGE_KEY = 'aio_notification_prefs'
const TOAST_TTL_MS = 5600
const MAX_TOASTS = 4

export type NotificationPrefs = {
  showOnDevice: boolean
  browserPush: boolean
  sound: boolean
  volume: number
  previewName: boolean
  previewText: boolean
  fromPrivate: boolean
  fromGroups: boolean
  fromSystem: boolean
}

export type AppToast = {
  id: string
  chatId: string
  title: string
  body: string
  avatarUrl: string | null
  brand: boolean
}

const DEFAULTS: NotificationPrefs = {
  showOnDevice: true,
  browserPush: true,
  sound: true,
  volume: 80,
  previewName: true,
  previewText: true,
  fromPrivate: true,
  fromGroups: true,
  fromSystem: true,
}

function load(): NotificationPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULTS }
    const parsed = JSON.parse(raw) as Partial<NotificationPrefs>
    return {
      ...DEFAULTS,
      ...parsed,
      volume: Math.min(100, Math.max(0, Number(parsed.volume ?? DEFAULTS.volume))),
    }
  } catch {
    return { ...DEFAULTS }
  }
}

function senderLabel(message: Message): string {
  const s = message.sender
  if (!s) return ''
  const full = [s.first_name, s.last_name].filter(Boolean).join(' ').trim()
  return full || s.username
}

function messageBody(message: Message): string {
  if (message.is_deleted) return ''
  if (message.content?.trim()) return message.content.trim()
  if (message.attachment) return message.attachment.original_filename || '📎'
  return ''
}

export const useNotificationStore = defineStore('notifications', () => {
  const prefs = reactive<NotificationPrefs>(load())
  const toasts = ref<AppToast[]>([])
  const timers = new Map<string, ReturnType<typeof setTimeout>>()

  const enabled = computed(() => prefs.showOnDevice)

  function set<K extends keyof NotificationPrefs>(key: K, value: NotificationPrefs[K]) {
    prefs[key] = value
  }

  function dismiss(id: string) {
    const timer = timers.get(id)
    if (timer) {
      clearTimeout(timer)
      timers.delete(id)
    }
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function clearAll() {
    for (const id of timers.keys()) clearTimeout(timers.get(id)!)
    timers.clear()
    toasts.value = []
  }

  function pushToast(toast: Omit<AppToast, 'id'> & { id?: string }) {
    const id = toast.id ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    toasts.value = [{ ...toast, id }, ...toasts.value].slice(0, MAX_TOASTS)
    const timer = setTimeout(() => dismiss(id), TOAST_TTL_MS)
    timers.set(id, timer)
    return id
  }

  function allowsChat(chat: Chat | undefined, message: Message): boolean {
    if (message.content_type === 'system') return prefs.fromSystem
    if (!chat) return prefs.fromPrivate
    if (chat.type === 'group') return prefs.fromGroups
    return prefs.fromPrivate
  }

  function buildPreview(message: Message): Pick<AppToast, 'title' | 'body' | 'avatarUrl' | 'brand'> {
    const locale = useLocaleStore()
    const rawName = senderLabel(message) || locale.t('notifHiddenSender')
    const rawBody = messageBody(message) || locale.t('notifDemoBody')
    const avatar = mediaUrl(message.sender?.avatar)

    if (!prefs.previewName) {
      return {
        title: locale.t('notifHiddenSender'),
        body: locale.t('notifHiddenBodyNoName'),
        avatarUrl: null,
        brand: true,
      }
    }

    return {
      title: rawName,
      body: prefs.previewText ? rawBody : locale.t('notifHiddenBodyNoText'),
      avatarUrl: avatar,
      brand: false,
    }
  }

  async function maybeBrowserNotify(toast: AppToast) {
    if (!prefs.browserPush) return
    if (typeof Notification === 'undefined') return
    if (Notification.permission !== 'granted') return
    if (!document.hidden) return

    try {
      const n = new Notification(toast.title, {
        body: toast.body,
        icon: toast.brand ? undefined : toast.avatarUrl || undefined,
        tag: `aio-chat-${toast.chatId}`,
        silent: true,
      })
      n.onclick = () => {
        window.focus()
        n.close()
        const chats = useChatsStore()
        void chats.selectChat(toast.chatId)
      }
    } catch {
      // Permission or OS restrictions — ignore.
    }
  }

  const recentlyNotified = new Set<string>()

  /** Incoming message → in-app toast (+ optional browser / sound). */
  function notifyFromMessage(message: Message) {
    if (!prefs.showOnDevice) return

    const auth = useAuthStore()
    if (!auth.user) return
    if (message.sender?.id === auth.user.id) return

    // Chat + inbox sockets can both deliver the same event.
    if (recentlyNotified.has(message.id)) return
    recentlyNotified.add(message.id)
    window.setTimeout(() => recentlyNotified.delete(message.id), 2500)

    const chats = useChatsStore()
    const chat = chats.chats.find((c) => c.id === message.chat)
    if (!allowsChat(chat, message)) return

    // Don't interrupt while the user is actively looking at this chat.
    if (chats.activeChatId === message.chat && !document.hidden) return

    const preview = buildPreview(message)
    const toast: AppToast = {
      id: `msg-${message.id}`,
      chatId: message.chat,
      ...preview,
    }

    dismiss(toast.id)
    pushToast(toast)

    if (prefs.sound) {
      void playNotifySound(prefs.volume)
    }
    void maybeBrowserNotify(toast)
  }

  async function ensureBrowserPermission(): Promise<NotificationPermission | 'unsupported'> {
    if (typeof Notification === 'undefined') return 'unsupported'
    if (Notification.permission === 'granted') return 'granted'
    if (Notification.permission === 'denied') return 'denied'
    try {
      return await Notification.requestPermission()
    } catch {
      return 'denied'
    }
  }

  watch(
    prefs,
    () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
    },
    { deep: true },
  )

  watch(
    () => prefs.browserPush,
    (on) => {
      if (on) void ensureBrowserPermission()
    },
  )

  return {
    prefs,
    enabled,
    toasts,
    set,
    dismiss,
    clearAll,
    pushToast,
    notifyFromMessage,
    ensureBrowserPermission,
  }
})
