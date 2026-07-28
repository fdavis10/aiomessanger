<script setup lang="ts">
import type { Message } from '@/types'
import { attachmentDownloadUrl } from '@/api/chats'
import { getAccessToken } from '@/api/client'
import { useLocaleStore } from '@/stores/locale'
import SnapText from '@/components/SnapText.vue'

const props = defineProps<{
  message: Message
  mine: boolean
}>()

const locale = useLocaleStore()

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(locale.locale === 'ru' ? 'ru-RU' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function downloadAttachment() {
  const att = props.message.attachment
  if (!att) return
  const token = getAccessToken()
  const res = await fetch(attachmentDownloadUrl(att.id), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: 'include',
  })
  if (!res.ok) return
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = att.original_filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="flex" :class="mine ? 'justify-end' : 'justify-start'">
    <div class="msg-bubble" :class="mine ? 'is-mine' : 'is-other'">
      <p
        v-if="!mine && message.sender"
        class="text-[0.7rem] uppercase tracking-wide opacity-70 mb-1"
      >
        {{ message.sender.username }}
      </p>
      <p v-if="message.is_deleted" class="italic opacity-60">
        <SnapText k="messageDeleted" />
      </p>
      <template v-else>
        <p class="whitespace-pre-wrap break-words leading-snug">{{ message.content }}</p>
        <button
          v-if="message.attachment"
          type="button"
          class="mt-2 text-sm underline underline-offset-2 opacity-90 hover:opacity-100"
          @click="downloadAttachment"
        >
          {{ message.attachment.original_filename }}
          ({{ Math.ceil(message.attachment.size_bytes / 1024) }} KB)
        </button>
      </template>
      <p class="text-[0.65rem] mt-1 opacity-60 text-right">
        {{ formatTime(message.created_at) }}
      </p>
    </div>
  </div>
</template>
