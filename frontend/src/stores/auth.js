import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin)
  const isVip = computed(() => user.value?.vip_expires_at && new Date(user.value.vip_expires_at) > new Date())

  async function fetchMe() {
    try { const res = await getMe(); user.value = res.data } catch { logout() }
  }

  function logout() { localStorage.clear(); user.value = null; window.location.href = '/login' }

  return { user, isLoggedIn, isAdmin, isVip, fetchMe, logout }
})
