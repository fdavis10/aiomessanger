<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useAttrs } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import { registerSnapTarget, unregisterSnapTarget } from '@/i18n/snap'
import type { MessageKey } from '@/i18n/messages'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    k?: MessageKey
    text?: string
    tag?: string
  }>(),
  { tag: 'span' },
)

const attrs = useAttrs()
const locale = useLocaleStore()
const root = ref<HTMLElement | null>(null)

const content = computed(() => {
  if (props.text !== undefined) return props.text
  if (props.k) return locale.t(props.k)
  return ''
})

onMounted(() => {
  if (root.value) registerSnapTarget(root.value)
})

onBeforeUnmount(() => {
  if (root.value) unregisterSnapTarget(root.value)
})
</script>

<template>
  <component :is="tag" ref="root" class="snap-text" v-bind="attrs">{{ content }}</component>
</template>
