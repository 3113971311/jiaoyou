import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe } from '../api'
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin)
  async function fetchMe() {
    try {
      const r = await getMe()
      user.value = r.data
      return true
    } catch {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_refresh_token')
      user.value = null
      return false
    }
  }
  function logout() {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
    user.value = null
    window.location.href = '/#/login'
  }
  return { user, isLoggedIn, isAdmin, fetchMe, logout }
})
