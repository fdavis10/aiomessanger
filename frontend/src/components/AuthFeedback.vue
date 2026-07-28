<script setup lang="ts">
import { watch } from 'vue'
import SnapText from '@/components/SnapText.vue'
import type { MessageKey } from '@/i18n/messages'

const props = defineProps<{
  status: 'success' | 'error' | null
  successKey?: MessageKey
  errorKey?: MessageKey
}>()

const emit = defineEmits<{
  done: []
  retry: []
}>()

watch(
  () => props.status,
  (next, _prev, onCleanup) => {
    if (next !== 'success') return
    const timer = window.setTimeout(() => emit('done'), 1450)
    onCleanup(() => window.clearTimeout(timer))
  },
)
</script>

<template>
  <Transition name="auth-feedback">
    <div
      v-if="status"
      class="auth-feedback"
      :class="status === 'success' ? 'is-success' : 'is-error'"
      role="status"
      aria-live="polite"
    >
      <div class="auth-feedback__panel">
        <div class="auth-feedback__mark" aria-hidden="true">
          <svg class="auth-feedback__svg" viewBox="0 0 64 64" fill="none">
            <circle class="auth-feedback__ring" cx="32" cy="32" r="28" />
            <path
              v-if="status === 'success'"
              class="auth-feedback__check"
              d="M18 33.5 L27.5 43 L46 22"
            />
            <g v-else class="auth-feedback__cross">
              <path d="M22 22 L42 42" />
              <path d="M42 22 L22 42" />
            </g>
          </svg>
        </div>

        <p class="auth-feedback__title">
          <SnapText
            :k="status === 'success' ? (successKey ?? 'authSuccess') : (errorKey ?? 'authInvalid')"
          />
        </p>

        <button
          v-if="status === 'error'"
          class="btn btn-primary auth-feedback__retry"
          type="button"
          @click="emit('retry')"
        >
          <SnapText k="authTryAgain" />
        </button>
      </div>
    </div>
  </Transition>
</template>
