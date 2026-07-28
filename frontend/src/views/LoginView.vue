<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLocaleStore } from '@/stores/locale'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LocaleSwitch from '@/components/LocaleSwitch.vue'
import SnapText from '@/components/SnapText.vue'
import AuthFeedback from '@/components/AuthFeedback.vue'

const auth = useAuthStore()
const locale = useLocaleStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const feedback = ref<'success' | 'error' | null>(null)

async function onSubmit() {
  if (feedback.value || auth.loading) return
  try {
    await auth.login(username.value.trim(), password.value)
    feedback.value = 'success'
  } catch {
    feedback.value = 'error'
  }
}

async function onSuccessDone() {
  await router.push({ name: 'messenger' })
}

function onRetry() {
  feedback.value = null
  auth.clearError()
}
</script>

<template>
  <div class="auth-shell">
    <form
      class="auth-card auth-card--login glass glass-strong"
      :class="{ 'is-shaking': feedback === 'error' }"
      @submit.prevent="onSubmit"
    >
      <AuthFeedback
        :status="feedback"
        success-key="authSuccess"
        error-key="authInvalid"
        @done="onSuccessDone"
        @retry="onRetry"
      />

      <div class="auth-top toolbar-switches">
        <LocaleSwitch />
        <ThemeToggle />
      </div>
      <p class="brand-mark text-[clamp(2.75rem,10vw,3.75rem)] mb-2">AIO</p>
      <p class="auth-lead text-[0.95rem] text-muted">
        <SnapText k="authLoginLead" />
      </p>

      <label class="block text-sm font-semibold mb-4">
        <SnapText k="username" />
        <input
          v-model="username"
          class="field"
          autocomplete="username"
          required
          :disabled="!!feedback || auth.loading"
        />
      </label>

      <label class="block text-sm font-semibold mb-5">
        <SnapText k="password" />
        <input
          v-model="password"
          type="password"
          class="field"
          autocomplete="current-password"
          required
          :disabled="!!feedback || auth.loading"
        />
      </label>

      <button
        class="btn btn-primary w-full mb-4"
        type="submit"
        :disabled="!!feedback || auth.loading"
      >
        <SnapText :text="auth.loading ? locale.t('signingIn') : locale.t('signIn')" />
      </button>

      <p class="auth-footer text-sm text-muted">
        <SnapText k="noAccount" />
        <RouterLink class="link-brand hover:underline" to="/register">
          <SnapText k="createOne" />
        </RouterLink>
      </p>
    </form>
  </div>
</template>
