<script setup lang="ts">
defineProps<{
  modelValue: boolean
  label: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<template>
  <label class="settings-toggle" :class="{ 'is-disabled': disabled }">
    <span class="settings-toggle__label">{{ label }}</span>
    <button
      type="button"
      class="settings-toggle__switch"
      role="switch"
      :aria-checked="modelValue"
      :aria-label="label"
      :disabled="disabled"
      @click="emit('update:modelValue', !modelValue)"
    >
      <span class="settings-toggle__thumb" />
    </button>
  </label>
</template>
