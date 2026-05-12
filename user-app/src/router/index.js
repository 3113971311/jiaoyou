import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/', component: () => import('../views/Home.vue'), meta: { requiresAuth: true } },
  { path: '/moments', component: () => import('../views/Moments.vue'), meta: { requiresAuth: true } },
  { path: '/moment/:id', component: () => import('../views/MomentDetail.vue'), meta: { requiresAuth: true } },
  { path: '/match', component: () => import('../views/Match.vue'), meta: { requiresAuth: true } },
  { path: '/chat', component: () => import('../views/Chats.vue'), meta: { requiresAuth: true } },
  { path: '/chat/:id', component: () => import('../views/ChatDetail.vue'), meta: { requiresAuth: true } },
  { path: '/vip', component: () => import('../views/Vip.vue'), meta: { requiresAuth: true } },
  { path: '/profile', component: () => import('../views/Profile.vue'), meta: { requiresAuth: true } },
  { path: '/profile/:id', component: () => import('../views/UserProfile.vue'), meta: { requiresAuth: true } },
  { path: '/notifications', component: () => import('../views/Notifications.vue'), meta: { requiresAuth: true } },
  { path: '/settings', component: () => import('../views/Settings.vue'), meta: { requiresAuth: true } },
  { path: '/buy-card', component: () => import('../views/BuyCard.vue'), meta: { requiresAuth: true } },
  { path: '/feedback', component: () => import('../views/Feedback.vue'), meta: { requiresAuth: true } },
  { path: '/verify', component: () => import('../views/Verify.vue'), meta: { requiresAuth: true } },
  { path: '/following', component: () => import('../views/Following.vue'), meta: { requiresAuth: true } },
  { path: '/followers', component: () => import('../views/Followers.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHashHistory(), routes })
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const token = localStorage.getItem('user_token')
  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.guest && token) return next('/')
  if (token && !auth.user) { try { await auth.fetchMe() } catch { return next('/login') } }
  next()
})
export default router
