import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe, getNotifications } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const unreadCount = ref(0)
  const latestNotif = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin)
  const isVip = computed(() => user.value?.vip_expires_at && new Date(user.value.vip_expires_at) > new Date())

  async function fetchMe() {
    try { const res = await getMe(); user.value = res.data } catch { logout() }
  }

  async function pollUnread() {
    try {
      const r = await getNotifications()
      unreadCount.value = r.data.unread_count || 0
      const items = r.data.items || []
      latestNotif.value = items.find(n => !n.is_read) || null
    } catch {}
  }

  function logout() { localStorage.clear(); user.value = null; window.location.href = '/login' }

  return { user, unreadCount, latestNotif, isLoggedIn, isAdmin, isVip, fetchMe, pollUnread, logout }
})
