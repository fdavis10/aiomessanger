<script setup lang="ts">
import { ref } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import SnapText from '@/components/SnapText.vue'

const locale = useLocaleStore()

const emit = defineEmits<{
  send: [content: string]
  upload: [file: File]
  typing: []
}>()

const draft = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

function submit() {
  const content = draft.value.trim()
  if (!content) return
  emit('send', content)
  draft.value = ''
}

function onInput() {
  emit('typing')
}

function pickFile() {
  fileInput.value?.click()
}

function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('upload', file)
  input.value = ''
}
</script>

<template>
  <form class="composer glass" @submit.prevent="submit">
    <input ref="fileInput" type="file" class="hidden" @change="onFileChange" />
    <button
      class="btn btn-ghost !px-3 !py-2 shrink-0"
      type="button"
      :title="locale.t('attachFile')"
      @click="pickFile"
    >
      +
    </button>
    <textarea
      v-model="draft"
      class="field !mt-0 flex-1 min-h-[2.75rem] max-h-32 resize-y"
      rows="1"
      :placeholder="locale.t('writeMessage')"
      @input="onInput"
      @keydown.enter.exact.prevent="submit"
    />
    <button class="btn btn-primary shrink-0" type="submit">
      <SnapText k="send" />
    </button>
  </form>
</template>
