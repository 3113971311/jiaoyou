import axios from 'axios'
const api = axios.create({ baseURL: '/api', timeout: 15000 })
const refreshClient = axios.create({ baseURL: '/api', timeout: 15000 })

let refreshPromise = null

function clearAdminAuth() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_refresh_token')
}

function shouldSkipRefresh(url = '') {
  return ['/auth/login', '/auth/refresh'].some((path) => url.includes(path))
}

async function refreshAdminToken() {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem('admin_refresh_token')
    if (!refreshToken) throw new Error('missing admin refresh token')
    refreshPromise = refreshClient.post('/auth/refresh', { refresh_token: refreshToken })
      .then((res) => {
        localStorage.setItem('admin_token', res.data.access_token)
        localStorage.setItem('admin_refresh_token', res.data.refresh_token)
        return res.data.access_token
      })
      .catch((error) => {
        clearAdminAuth()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {}
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !shouldSkipRefresh(originalRequest.url)
    ) {
      originalRequest._retry = true
      try {
        const token = await refreshAdminToken()
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      } catch (refreshError) {
        clearAdminAuth()
        window.location.href = '/#/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)
export default api
export const login = (d) => api.post('/auth/login', d)
export const getMe = () => api.get('/auth/me')
export const getUser = (id) => api.get(`/users/${id}`)
export const adminDashboard = () => api.get('/admin/dashboard')
export const adminListUsers = (p) => api.get('/admin/users', { params: p })
export const adminCreateUser = (d) => api.post('/admin/users', d)
export const adminUpdateUser = (id, d) => api.put(`/admin/users/${id}`, d)
export const adminToggleStatus = (id, d) => api.put(`/admin/users/${id}/status`, d)
export const adminRemoveVip = (id) => api.post(`/admin/users/${id}/remove-vip`)
export const adminDeleteUser = (id) => api.delete(`/admin/users/${id}`)
export const adminWarnUser = (id, d) => api.post(`/admin/users/${id}/warn`, d)
export const adminUserWarnings = (id) => api.get(`/admin/users/${id}/warnings`)
export const adminReviewQueue = (p) => api.get('/admin/review-queue', { params: p })
export const adminApprove = (id) => api.post(`/admin/review-queue/${id}/approve`)
export const adminReject = (id, d) => api.post(`/admin/review-queue/${id}/reject`, d)
export const adminBatchReview = (d) => api.post('/admin/review-queue/batch', d)
export const adminBatchDelete = (d) => api.post('/admin/review-queue/batch-delete', d)
export const adminGenerateCards = (d) => api.post('/admin/cards/generate', d)
export const adminListBatches = () => api.get('/admin/cards/batches')
export const adminBatchDetail = (id, p) => api.get(`/admin/cards/batches/${id}`, { params: p })
export const adminDeleteCard = (id) => api.delete(`/admin/cards/${id}`)
export const adminExportBatch = (id) => api.get(`/admin/cards/batches/${id}/export`)
export const adminDeleteBatch = (id) => api.delete(`/admin/cards/batches/${id}`)
export const adminChats = () => api.get('/admin/chats')
export const adminChatMsgs = (id) => api.get(`/admin/chats/${id}/messages`)
export const adminReports = (p) => api.get('/admin/reports', { params: p })
export const adminHandleReport = (id, d) => api.post(`/admin/reports/${id}/handle`, d)
export const adminSiteConfigs = () => api.get('/admin/site-configs')
export const adminUpdateConfig = (key, d) => api.put(`/admin/site-configs/${key}`, d)
export const adminVipPlans = () => api.get('/admin/vip-plans')
export const adminCreateVipPlan = (d) => api.post('/admin/vip-plans', d)
export const adminUpdateVipPlan = (id, d) => api.put(`/admin/vip-plans/${id}`, d)
export const adminDeleteVipPlan = (id) => api.delete(`/admin/vip-plans/${id}`)
export const adminUploadVipPlanQr = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/admin/vip-plans/upload-qr', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}
export const adminAlipayLogin = () => api.post('/admin/alipay/login')
export const adminSyncAlipayBills = () => api.post('/admin/alipay/bills/sync', null, { timeout: 70000 })
export const adminAlipayBills = (p) => api.get('/admin/alipay/bills', { params: p })
export const adminAlipayBillDetail = (id) => api.get(`/admin/alipay/bills/${id}`)
export const adminBatchAlipayBillStatus = (d) => api.post('/admin/alipay/bills/batch-status', d)
export const adminListMoments = (p) => api.get('/admin/moments', { params: p })
export const adminGetMoment = (id) => api.get(`/admin/moments/${id}`)
export const adminUpdateMoment = (id, d) => api.put(`/admin/moments/${id}`, d)
export const adminDeleteMoment = (id) => api.delete(`/admin/moments/${id}`)
export const adminReviewMoment = (id, d) => api.post(`/admin/moments/${id}/review`, d)
export const adminImageUrl = (p) => { const t = localStorage.getItem('admin_token')||''; return `/api/admin/image-preview?path=${encodeURIComponent(p)}&token=${t}` }
