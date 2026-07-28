<script setup lang="ts">
import { useLocaleStore } from '@/stores/locale'

const locale = useLocaleStore()

async function onToggle() {
  if (locale.snapping) return
  await locale.toggle()
}
</script>

<template>
  <button
    type="button"
    class="locale-switch"
    :class="{ 'is-busy': locale.snapping }"
    :disabled="locale.snapping"
    :aria-label="locale.isRu ? locale.t('langToEn') : locale.t('langToRu')"
    :title="locale.isRu ? locale.t('langToEn') : locale.t('langToRu')"
    @click="onToggle"
  >
    <span class="locale-switch__option" :class="{ 'is-active': locale.isRu }">RU</span>
    <span class="locale-switch__track" aria-hidden="true">
      <span class="locale-switch__thumb" :class="{ 'is-en': !locale.isRu }" />
    </span>
    <span class="locale-switch__option" :class="{ 'is-active': !locale.isRu }">EN</span>
  </button>
</template>
