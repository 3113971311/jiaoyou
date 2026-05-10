import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/', component: () => import('../views/Home.vue'), meta: { requiresAuth: true } },
  { path: '/moments', component: () => import('../views/Moments.vue'), meta: { requiresAuth: true } },
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
  { path: '/following', component: () => import('../views/Following.vue'), meta: { requiresAuth: true } },
  { path: '/followers', component: () => import('../views/Followers.vue'), meta: { requiresAuth: true } },
  { path: '/admin/login', component: () => import('../views/admin/AdminLogin.vue'), meta: { guest: true } },
  { path: '/admin', component: () => import('../views/admin/AdminLayout.vue'), meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', component: () => import('../views/admin/AdminDashboard.vue') },
      { path: 'review', component: () => import('../views/admin/AdminReview.vue') },
      { path: 'cards', component: () => import('../views/admin/AdminCards.vue') },
      { path: 'users', component: () => import('../views/admin/AdminUsers.vue') },
      { path: 'chats', component: () => import('../views/admin/AdminChats.vue') },
      { path: 'reports', component: () => import('../views/admin/AdminReports.vue') },
      { path: 'settings', component: () => import('../views/admin/AdminSettings.vue') },
    ]
  },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.guest && token) return next('/')
  if (token && !auth.user) {
    try { await auth.fetchMe() } catch { auth.logout(); return next('/login') }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) { ElMessage?.warning?.('需要管理员权限'); return next('/') }
  next()
})

export default router
