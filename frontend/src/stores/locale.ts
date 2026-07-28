import { defineStore } from 'pinia'
import { computed, nextTick, ref, watch } from 'vue'
import { messages, type Locale, type MessageKey } from '@/i18n/messages'
import {
  appearTargets,
  dissolveTargets,
  prefersReducedMotion,
} from '@/i18n/snap'

const STORAGE_KEY = 'aio_locale'

function detectInitial(): Locale {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'ru' || saved === 'en') return saved
  const nav = navigator.language.toLowerCase()
  return nav.startsWith('ru') ? 'ru' : 'en'
}

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<Locale>(detectInitial())
  const snapping = ref(false)

  const isRu = computed(() => locale.value === 'ru')

  function t(key: MessageKey): string {
    return messages[locale.value][key]
  }

  async function setLocale(next: Locale) {
    if (next === locale.value || snapping.value) return

    if (prefersReducedMotion()) {
      locale.value = next
      return
    }

    snapping.value = true
    try {
      await dissolveTargets()
      locale.value = next
      await nextTick()
      await appearTargets()
    } finally {
      snapping.value = false
    }
  }

  async function toggle() {
    await setLocale(locale.value === 'ru' ? 'en' : 'ru')
  }

  watch(
    locale,
    (next) => {
      localStorage.setItem(STORAGE_KEY, next)
      document.documentElement.setAttribute('lang', next)
    },
    { immediate: true },
  )

  return { locale, isRu, snapping, t, setLocale, toggle }
})
