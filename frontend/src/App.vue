<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import ToastNotifications from '@/components/ToastNotifications.vue'

const theme = useThemeStore()
onMounted(() => {
  // Ensure theme is applied even if store hydrated before DOM paint.
  document.documentElement.setAttribute('data-theme', theme.mode)
})
</script>

<template>
  <div class="app-shell">
    <RouterView />
    <ToastNotifications />
  </div>
</template>
