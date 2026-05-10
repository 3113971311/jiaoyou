import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import client from '../api/client';
import router from '../router';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null);
  const isVip = computed(() => {
    if (!user.value?.vipExpiresAt) return false;
    return new Date(user.value.vipExpiresAt) > new Date();
  });
  const isLoggedIn = computed(() => !!user.value && !!localStorage.getItem('accessToken'));

  async function login(account: string, password: string) {
    const res = await client.post('/auth/login', { account, password });
    localStorage.setItem('accessToken', res.data.accessToken);
    localStorage.setItem('refreshToken', res.data.refreshToken);
    await fetchMe();
    return res.data;
  }

  async function fetchMe() {
    try {
      const res = await client.get('/auth/me');
      user.value = res.data;
    } catch {
      logout();
    }
  }

  function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    user.value = null;
    router.push('/login');
  }

  return { user, isVip, isLoggedIn, login, fetchMe, logout };
});
