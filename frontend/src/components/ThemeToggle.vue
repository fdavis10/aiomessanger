<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { useLocaleStore } from '@/stores/locale'

const theme = useThemeStore()
const locale = useLocaleStore()

const label = computed(() =>
  theme.isDark ? locale.t('themeToLight') : locale.t('themeToDark'),
)

async function onToggle() {
  if (theme.transitioning) return
  await theme.toggle()
}
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :class="{ 'is-busy': theme.transitioning }"
    :disabled="theme.transitioning"
    :aria-label="label"
    :title="label"
    @click="onToggle"
  >
    <span class="theme-toggle__thumb" :class="{ 'is-light': !theme.isDark }" />
  </button>
</template>
