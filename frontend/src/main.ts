import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useLocaleStore } from './stores/locale'
import './style.css'
import './styles/settings.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

useThemeStore(pinia)
useLocaleStore(pinia)

const auth = useAuthStore(pinia)
auth.bootstrap().finally(() => {
  app.mount('#app')
})
