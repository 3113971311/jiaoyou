import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Home.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/moments',
      name: 'moments',
      component: () => import('../views/Moments.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/match',
      name: 'match',
      component: () => import('../views/Match.vue'),
      meta: { requiresAuth: true, requiresVip: true },
    },
    {
      path: '/chat',
      name: 'chats',
      component: () => import('../views/Chats.vue'),
      meta: { requiresAuth: true, requiresVip: true },
    },
    {
      path: '/chat/:id',
      name: 'chatDetail',
      component: () => import('../views/ChatDetail.vue'),
      meta: { requiresAuth: true, requiresVip: true },
    },
    {
      path: '/vip',
      name: 'vip',
      component: () => import('../views/Vip.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/buy-card',
      name: 'buyCard',
      component: () => import('../views/BuyCard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile/:id',
      name: 'userProfile',
      component: () => import('../views/UserProfile.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../views/Notifications.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/Settings.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/following',
      name: 'following',
      component: () => import('../views/Following.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/followers',
      name: 'followers',
      component: () => import('../views/Followers.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: () => import('../views/Feedback.vue'),
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  const token = localStorage.getItem('accessToken');

  if (to.meta.requiresAuth && !token) {
    return next('/login');
  }

  if (to.meta.guest && token) {
    return next('/');
  }

  // 自动拉取用户信息
  if (token && !auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      return next('/login');
    }
  }

  // VIP 检查
  if (to.meta.requiresVip && !auth.isVip) {
    return next('/vip');
  }

  next();
});

export default router;
