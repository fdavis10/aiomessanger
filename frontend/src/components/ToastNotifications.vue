<script setup lang="ts">
import { useNotificationStore } from '@/stores/notifications'
import { useChatsStore } from '@/stores/chats'
import { useLocaleStore } from '@/stores/locale'

const notif = useNotificationStore()
const chats = useChatsStore()
const locale = useLocaleStore()

async function onOpen(toastId: string, chatId: string) {
  notif.dismiss(toastId)
  await chats.selectChat(chatId)
}

function onClose(ev: Event, toastId: string) {
  ev.stopPropagation()
  notif.dismiss(toastId)
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-relevant="additions">
      <TransitionGroup name="toast-pop">
        <article
          v-for="toast in notif.toasts"
          :key="toast.id"
          class="app-toast"
          role="status"
          @click="onOpen(toast.id, toast.chatId)"
        >
          <button
            type="button"
            class="app-toast__close"
            :aria-label="locale.t('profileClose')"
            @click="onClose($event, toast.id)"
          >
            ×
          </button>

          <div class="app-toast__avatar" :class="{ 'is-brand': toast.brand }" aria-hidden="true">
            <img v-if="toast.avatarUrl && !toast.brand" :src="toast.avatarUrl" alt="" />
            <span v-else-if="toast.brand">A</span>
            <span v-else>{{ toast.title.slice(0, 1).toUpperCase() }}</span>
          </div>

          <div class="app-toast__text">
            <p class="app-toast__name">{{ toast.title }}</p>
            <p class="app-toast__body">{{ toast.body }}</p>
          </div>
        </article>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
