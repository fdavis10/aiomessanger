<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useLocaleStore } from '@/stores/locale'
import ThemeToggle from '@/components/ThemeToggle.vue'
import SnapText from '@/components/SnapText.vue'
import NavGlyph from '@/components/NavGlyph.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  close: []
  logout: []
  navigate: [item: 'profile' | 'group' | 'calls' | 'settings']
}>()

const auth = useAuthStore()
const locale = useLocaleStore()

const initials = computed(() => {
  const name = auth.user?.username?.trim() || '?'
  return name.slice(0, 2).toUpperCase()
})

function onKey(ev: KeyboardEvent) {
  if (ev.key === 'Escape' && props.open) emit('close')
}

watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div class="side-drawer-root" :class="{ 'is-open': open }">
      <button
        type="button"
        class="side-drawer__backdrop"
        :aria-label="locale.t('closeMenu')"
        tabindex="-1"
        @click="emit('close')"
      />

      <aside
        class="side-drawer glass glass-strong"
        role="dialog"
        aria-modal="true"
        :aria-hidden="!open"
        :aria-label="locale.t('openMenu')"
      >
        <header class="side-drawer__profile">
          <div class="side-drawer__avatar" aria-hidden="true">
            <img
              v-if="auth.user?.avatar"
              :src="auth.user.avatar"
              alt=""
              class="side-drawer__avatar-img"
            />
            <span v-else class="side-drawer__avatar-fall">{{ initials }}</span>
          </div>
          <p class="side-drawer__nick">{{ auth.user?.username }}</p>
          <p v-if="auth.user?.id" class="side-drawer__meta">ID {{ auth.user.id }}</p>
        </header>

        <nav class="side-drawer__nav">
          <button type="button" class="side-drawer__item" @click="emit('navigate', 'profile')">
            <NavGlyph name="profile" />
            <span class="side-drawer__label"><SnapText k="menuProfile" /></span>
          </button>
          <button type="button" class="side-drawer__item" @click="emit('navigate', 'group')">
            <NavGlyph name="group" />
            <span class="side-drawer__label"><SnapText k="menuCreateGroup" /></span>
          </button>
          <button type="button" class="side-drawer__item" @click="emit('navigate', 'calls')">
            <NavGlyph name="calls" />
            <span class="side-drawer__label"><SnapText k="menuCalls" /></span>
          </button>
          <button type="button" class="side-drawer__item" @click="emit('navigate', 'settings')">
            <NavGlyph name="settings" />
            <span class="side-drawer__label"><SnapText k="menuSettings" /></span>
          </button>

          <div class="side-drawer__item side-drawer__item--theme">
            <NavGlyph name="theme" />
            <span class="side-drawer__label"><SnapText k="menuTheme" /></span>
            <ThemeToggle class="side-drawer__theme-toggle" />
          </div>
        </nav>

        <footer class="side-drawer__footer">
          <button type="button" class="side-drawer__item side-drawer__logout" @click="emit('logout')">
            <NavGlyph name="logout" />
            <span class="side-drawer__label"><SnapText k="logout" /></span>
          </button>
        </footer>
      </aside>
    </div>
  </Teleport>
</template>
