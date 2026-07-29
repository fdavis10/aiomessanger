<script setup lang="ts">
import { computed, onMounted, ref, toRef } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatsStore } from '@/stores/chats'
import { useLocaleStore } from '@/stores/locale'
import { useChatSocket } from '@/composables/useChatSocket'
import { useInboxSocket } from '@/composables/useInboxSocket'
import * as chatsApi from '@/api/chats'
import ChatList from '@/components/ChatList.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import SideDrawer from '@/components/SideDrawer.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import SettingsPanel from '@/components/SettingsPanel.vue'
import SnapText from '@/components/SnapText.vue'

const auth = useAuthStore()
const chats = useChatsStore()
const locale = useLocaleStore()
const router = useRouter()
const peerUserId = ref('')
const menuOpen = ref(false)
const profileOpen = ref(false)
const settingsOpen = ref(false)
const soonHint = ref<string | null>(null)

const chatId = toRef(chats, 'activeChatId')
const { connected, sendMessage, notifyTyping } = useChatSocket(chatId)

const inboxEnabled = computed(() => auth.isAuthenticated)
const membershipKey = computed(() =>
  chats.chats
    .map((c) => c.id)
    .sort()
    .join(','),
)
useInboxSocket(inboxEnabled, membershipKey)

const chatOpen = computed(() => !!chats.activeChatId)

onMounted(() => {
  void chats.loadChats()
})

async function onLogout() {
  menuOpen.value = false
  profileOpen.value = false
  settingsOpen.value = false
  await auth.logout()
  await router.push({ name: 'login' })
}

async function startPrivateChat() {
  const id = Number(peerUserId.value)
  if (!Number.isFinite(id) || id <= 0) return
  await chats.createPrivate(id)
  peerUserId.value = ''
}

function onBack() {
  chats.activeChatId = null
}

async function onUpload(file: File) {
  if (!chats.activeChatId) return
  const message = await chatsApi.uploadAttachment(chats.activeChatId, file)
  chats.upsertMessage(message)
}

function showSoon() {
  soonHint.value = locale.t('menuSoon')
  window.setTimeout(() => {
    if (soonHint.value === locale.t('menuSoon')) soonHint.value = null
  }, 1800)
}

function onNavigate(item: 'profile' | 'group' | 'calls' | 'settings') {
  if (item === 'profile') {
    menuOpen.value = false
    profileOpen.value = true
    void auth.refreshMe().catch(() => undefined)
    return
  }
  if (item === 'settings') {
    menuOpen.value = false
    settingsOpen.value = true
    return
  }
  showSoon()
}

function onProfileEdit() {
  profileOpen.value = false
  settingsOpen.value = true
}
</script>

<template>
  <div class="messenger" :class="{ 'chat-open': chatOpen }">
    <aside class="chat-list-pane glass">
      <header class="chat-list-header">
        <button
          type="button"
          class="burger-btn"
          :aria-label="locale.t('openMenu')"
          :aria-expanded="menuOpen"
          @click="menuOpen = true"
        >
          <span class="burger-btn__line" />
          <span class="burger-btn__line" />
          <span class="burger-btn__line" />
        </button>
        <p class="brand-mark text-2xl">AIO</p>
      </header>

      <form class="px-4 pb-3 flex gap-2" @submit.prevent="startPrivateChat">
        <input
          v-model="peerUserId"
          class="field !mt-0 flex-1"
          :placeholder="locale.t('userIdDm')"
          inputmode="numeric"
        />
        <button class="btn btn-primary shrink-0" type="submit">
          <SnapText k="chat" />
        </button>
      </form>

      <ChatList />
    </aside>

    <section class="chat-window-pane glass glass-strong">
      <ChatWindow
        :connected="connected"
        @back="onBack"
        @send="sendMessage"
        @upload="onUpload"
        @typing="notifyTyping"
      />
    </section>

    <SideDrawer
      :open="menuOpen"
      @close="menuOpen = false"
      @logout="onLogout"
      @navigate="onNavigate"
    />

    <ProfileCard
      :open="profileOpen"
      :user="auth.user"
      @close="profileOpen = false"
      @edit="onProfileEdit"
    />

    <SettingsPanel :open="settingsOpen" @close="settingsOpen = false" />

    <Transition name="soon-hint">
      <p v-if="soonHint" class="soon-hint glass">{{ soonHint }}</p>
    </Transition>
  </div>
</template>
