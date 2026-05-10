import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes: [
    { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
    { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { requiresAuth: true } },
    { path: '/review', name: 'review', component: () => import('../views/ReviewQueue.vue'), meta: { requiresAuth: true } },
    { path: '/cards', name: 'cards', component: () => import('../views/CardBatches.vue'), meta: { requiresAuth: true } },
    { path: '/users', name: 'users', component: () => import('../views/Users.vue'), meta: { requiresAuth: true } },
    { path: '/chats', name: 'chats', component: () => import('../views/ChatMonitor.vue'), meta: { requiresAuth: true } },
    { path: '/reports', name: 'reports', component: () => import('../views/Reports.vue'), meta: { requiresAuth: true } },
    { path: '/sensitive', name: 'sensitive', component: () => import('../views/SensitiveWords.vue'), meta: { requiresAuth: true } },
    { path: '/config', name: 'config', component: () => import('../views/SiteConfig.vue'), meta: { requiresAuth: true } },
  ],
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('adminToken');
  if (to.meta.requiresAuth && !token) return next('/login');
  if (to.path === '/login' && token) return next('/');
  next();
});

export default router;
