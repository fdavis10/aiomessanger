import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'messenger',
      component: () => import('@/views/MessengerView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const authed = !!getAccessToken()
  if (to.meta.requiresAuth && !authed) return { name: 'login' }
  if (to.meta.guest && authed) return { name: 'messenger' }
  return true
})

export default router
