<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import SnapText from '@/components/SnapText.vue'

defineProps<{
  open: boolean
  titleKey: 'choiceBannerTitle' | 'choiceAvatarTitle'
}>()

const emit = defineEmits<{
  close: []
  upload: []
  generate: []
}>()

const locale = useLocaleStore()

function onKey(ev: KeyboardEvent) {
  if (ev.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <Transition name="choice-sheet">
      <div v-if="open" class="choice-sheet-root" @click.self="emit('close')">
        <div class="choice-sheet glass glass-strong" role="dialog" aria-modal="true">
          <p class="choice-sheet__title"><SnapText :k="titleKey" /></p>
          <button type="button" class="choice-sheet__btn" @click="emit('upload')">
            <SnapText k="choiceUpload" />
          </button>
          <button type="button" class="choice-sheet__btn choice-sheet__btn--accent" @click="emit('generate')">
            <SnapText k="choiceGenerate" />
          </button>
          <button type="button" class="choice-sheet__btn choice-sheet__btn--ghost" @click="emit('close')">
            {{ locale.t('profileClose') }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
