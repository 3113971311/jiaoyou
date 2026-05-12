import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/', component: () => import('../views/Layout.vue'), meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', component: () => import('../views/Dashboard.vue') },
      { path: 'review', component: () => import('../views/ReviewQueue.vue') },
      { path: 'moments', component: () => import('../views/Moments.vue') },
      { path: 'cards', component: () => import('../views/CardBatches.vue') },
      { path: 'users', component: () => import('../views/Users.vue') },
      { path: 'chats', component: () => import('../views/ChatMonitor.vue') },
      { path: 'reports', component: () => import('../views/Reports.vue') },
      { path: 'settings', component: () => import('../views/SiteConfig.vue') },
    ]
  },
]
const router = createRouter({ history: createWebHashHistory(), routes })
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.guest && token) return next('/')
  const auth = useAuthStore()
  if (token && !auth.user) { try { await auth.fetchMe() } catch { return next('/login') } }
  if (to.meta.requiresAdmin && !auth.isAdmin) { auth.logout(); return }
  next()
})
export default router
