import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { playThemeWipe, prefersReducedMotion } from '@/utils/themeWipe'

export type ThemeMode = 'dark' | 'light'

const STORAGE_KEY = 'aio_theme'

function detectInitial(): ThemeMode {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function applyTheme(mode: ThemeMode) {
  document.documentElement.setAttribute('data-theme', mode)
  document.documentElement.style.colorScheme = mode
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(detectInitial())
  const transitioning = ref(false)
  applyTheme(mode.value)

  const isDark = computed(() => mode.value === 'dark')

  async function setTheme(next: ThemeMode) {
    if (next === mode.value || transitioning.value) return

    if (prefersReducedMotion()) {
      mode.value = next
      return
    }

    transitioning.value = true
    try {
      await playThemeWipe(next, () => {
        mode.value = next
      })
    } finally {
      transitioning.value = false
    }
  }

  async function toggle() {
    await setTheme(mode.value === 'dark' ? 'light' : 'dark')
  }

  watch(
    mode,
    (next) => {
      localStorage.setItem(STORAGE_KEY, next)
      applyTheme(next)
    },
    { immediate: true },
  )

  return { mode, isDark, transitioning, setTheme, toggle }
})
