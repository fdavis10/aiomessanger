<script setup lang="ts">
import { useChatsStore } from '@/stores/chats'
import { useLocaleStore } from '@/stores/locale'
import SnapText from '@/components/SnapText.vue'

const chats = useChatsStore()
const locale = useLocaleStore()

function preview(chatId: string): string {
  const list = chats.messagesByChat[chatId]
  if (!list?.length) return locale.t('noMessagesYet')
  const last = list[list.length - 1]
  if (last.is_deleted || !last.content) return locale.t('messageDeleted')
  return last.content
}

function isUiPreview(chatId: string): boolean {
  const list = chats.messagesByChat[chatId]
  if (!list?.length) return true
  const last = list[list.length - 1]
  return last.is_deleted || !last.content
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(locale.locale === 'ru' ? 'ru-RU' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="scroll-y flex-1 px-2 pb-4">
    <p v-if="chats.loadingChats" class="px-3 py-2 text-sm text-muted">
      <SnapText k="loadingChats" />
    </p>
    <p v-else-if="!chats.chats.length" class="px-3 py-2 text-sm text-muted">
      <SnapText k="noChats" />
    </p>

    <button
      v-for="chat in chats.chats"
      :key="chat.id"
      type="button"
      class="chat-item"
      :class="{ 'is-active': chat.id === chats.activeChatId }"
      @click="chats.selectChat(chat.id)"
    >
      <div class="flex items-baseline justify-between gap-2">
        <SnapText class="font-semibold truncate" :text="chats.chatTitle(chat)" />
        <span class="text-xs text-faint shrink-0">{{ formatTime(chat.updated_at) }}</span>
      </div>
      <p class="text-sm text-muted truncate mt-0.5">
        <SnapText v-if="isUiPreview(chat.id)" :text="preview(chat.id)" />
        <template v-else>{{ preview(chat.id) }}</template>
      </p>
    </button>
  </div>
</template>
