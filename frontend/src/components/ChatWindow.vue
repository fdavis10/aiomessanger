<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatsStore } from '@/stores/chats'
import { useLocaleStore } from '@/stores/locale'
import MessageBubble from '@/components/MessageBubble.vue'
import MessageInput from '@/components/MessageInput.vue'
import SnapText from '@/components/SnapText.vue'

defineProps<{ connected: boolean }>()
const emit = defineEmits<{
  back: []
  send: [content: string]
  upload: [file: File]
  typing: []
}>()

const auth = useAuthStore()
const chats = useChatsStore()
const locale = useLocaleStore()
const scroller = ref<HTMLElement | null>(null)

const typingLabel = computed(() => {
  if (!chats.activeChatId) return ''
  const ids = chats.typingUsers[chats.activeChatId] ?? []
  if (!ids.length || !chats.activeChat) return ''
  const names = ids
    .map((id) => chats.activeChat?.members.find((m) => m.user.id === id)?.user.username)
    .filter(Boolean)
  if (!names.length) return locale.t('someoneTyping')
  return `${names.join(', ')} ${locale.t('typing')}`
})

watch(
  () => chats.activeMessages.length,
  async () => {
    await nextTick()
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  },
)
</script>

<template>
  <div v-if="!chats.activeChat" class="flex-1 grid place-items-center px-6 text-center">
    <div>
      <p class="brand-mark text-4xl mb-2">AIO</p>
      <p class="text-muted max-w-xs mx-auto text-sm">
        <SnapText k="selectChat" />
      </p>
    </div>
  </div>

  <template v-else>
    <header class="px-4 py-3 flex items-center gap-3 border-b border-[color:var(--border)]">
      <button
        class="btn btn-ghost md:hidden !px-2 !py-1"
        type="button"
        :aria-label="locale.t('back')"
        @click="emit('back')"
      >
        ←
      </button>
      <div class="min-w-0 flex-1">
        <p class="font-semibold truncate">
          <SnapText :text="chats.chatTitle(chats.activeChat)" />
        </p>
        <p class="text-xs text-muted">
          <SnapText
            :class="connected ? 'live-dot' : 'text-warn'"
            :text="connected ? locale.t('live') : locale.t('reconnecting')"
          />
          <span v-if="typingLabel"> · {{ typingLabel }}</span>
        </p>
      </div>
    </header>

    <div ref="scroller" class="scroll-y flex-1 px-4 py-4 space-y-2.5">
      <p v-if="chats.loadingMessages" class="text-sm text-muted">
        <SnapText k="loadingMessages" />
      </p>
      <MessageBubble
        v-for="message in chats.activeMessages"
        :key="message.id"
        :message="message"
        :mine="message.sender?.id === auth.user?.id"
      />
    </div>

    <MessageInput
      @send="emit('send', $event)"
      @upload="emit('upload', $event)"
      @typing="emit('typing')"
    />
  </template>
</template>
