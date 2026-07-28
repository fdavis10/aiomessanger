import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import { getAccessToken, clearTokens } from '@/api/client'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value && !!getAccessToken())

  async function bootstrap() {
    if (!getAccessToken()) return
    loading.value = true
    try {
      user.value = await authApi.fetchMe()
    } catch {
      clearTokens()
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    error.value = null
    try {
      user.value = await authApi.login(username, password)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, password: string, email = '') {
    loading.value = true
    error.value = null
    try {
      user.value = await authApi.register(username, password, email)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Registration failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await authApi.logout()
    user.value = null
  }

  async function refreshMe() {
    if (!getAccessToken()) return
    user.value = await authApi.fetchMe()
  }

  async function updateProfile(patch: authApi.ProfileUpdate) {
    user.value = await authApi.updateMe(patch)
    return user.value
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    bootstrap,
    login,
    register,
    logout,
    refreshMe,
    updateProfile,
    clearError,
  }
})
