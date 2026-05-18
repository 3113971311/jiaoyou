import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api', timeout: 15000 })
const refreshClient = axios.create({ baseURL: '/api', timeout: 15000 })
let refreshPromise = null

function clearUserAuth() {
  localStorage.removeItem('user_token')
  localStorage.removeItem('user_refresh_token')
}

function shouldSkipRefresh(url = '') {
  return [
    '/auth/login',
    '/auth/register',
    '/auth/send-verify-code',
    '/auth/reset-password',
    '/auth/refresh',
  ].some((path) => url.includes(path))
}

async function refreshUserToken() {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem('user_refresh_token')
    if (!refreshToken) throw new Error('missing user refresh token')
    refreshPromise = refreshClient.post('/auth/refresh', { refresh_token: refreshToken })
      .then((res) => {
        localStorage.setItem('user_token', res.data.access_token)
        localStorage.setItem('user_refresh_token', res.data.refresh_token)
        return res.data.access_token
      })
      .catch((error) => {
        clearUserAuth()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.request.use(c => {
  const token = localStorage.getItem('user_token')
  if (token) c.headers.Authorization = `Bearer ${token}`
  return c
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
        const token = await refreshUserToken()
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      } catch (refreshError) {
        clearUserAuth()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)

// Auth
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const sendCode = (data) => api.post('/auth/send-verify-code', data)
export const resetPwd = (data) => api.post('/auth/reset-password', data)
export const changePwd = (data) => api.put('/auth/password', data)
export const getMe = () => api.get('/auth/me')

// Users
export const getUser = (id) => api.get(`/users/${id}`)
export const updateProfile = (data) => api.put('/users/profile', data)
export const uploadAvatar = (data) => api.post('/users/avatar', data)

// Follow
export const follow = (id) => api.post(`/follow/${id}`)
export const unfollow = (id) => api.delete(`/follow/${id}`)
export const getFollowing = () => api.get('/follow/following')
export const getFollowers = () => api.get('/follow/followers')
export const followStatus = (id) => api.get(`/follow/status/${id}`)

// Moments
export const createMoment = (data) => api.post('/moments', data)
export const getFeed = (params) => api.get('/moments', { params })
export const getMoment = (id) => api.get(`/moments/${id}`)
export const deleteMoment = (id) => api.delete(`/moments/${id}`)
export const toggleLike = (id) => api.post(`/moments/${id}/like`)
export const toggleFavorite = (id) => api.post(`/moments/${id}/favorite`)
export const myLikes = (params) => api.get('/users/me/likes', { params })
export const myFavorites = (params) => api.get('/users/me/favorites', { params })
export const addComment = (id, data) => api.post(`/moments/${id}/comments`, data)
export const getComments = (id) => api.get(`/moments/${id}/comments`)
export const deleteComment = (momentId, commentId) => api.delete(`/moments/${momentId}/comments/${commentId}`)

// Match
export const startMatch = (data) => api.post('/match/start', data)
export const cancelMatch = () => api.post('/match/cancel')
export const matchStatus = () => api.get('/match/status')
export const matchHistory = () => api.get('/match/history')

// Chat
export const getConversations = () => api.get('/conversations')
export const getMessages = (id) => api.get(`/conversations/${id}/messages`)
export const createConversation = (data) => api.post('/conversations', data)
export const uploadChatImage = (data) => api.post('/upload/chat-image', data)

// Payment
export const redeemCard = (data) => api.post('/cards/redeem', data)
export const vipStatus = () => api.get('/vip/status')
export const vipHistory = () => api.get('/vip/history')
export const vipPlans = () => api.get('/vip/plans')
export const createPaymentOrder = (params) => api.post('/payment/orders', null, { params })
export const alipayPay = (data) => api.post('/payment/alipay/pay', data)
export const devPay = (data) => api.post('/payment/dev-pay', data)
export const getPaymentOrder = (id) => api.get(`/payment/orders/${id}`)
export const submitPaymentOrderNo = (id, data) => api.post(`/payment/orders/${id}/submit-order-no`, data, { timeout: 70000 })

// Reports
export const submitReport = (data) => api.post('/reports', data)
export const blockUser = (id) => api.post(`/blacklist/${id}`)
export const unblockUser = (id) => api.delete(`/blacklist/${id}`)
export const getBlacklist = () => api.get('/blacklist')

// Notifications
export const getNotifications = () => api.get('/notifications')
export const markRead = (id) => api.put(`/notifications/${id}/read`)
export const markAllRead = () => api.put('/notifications/read-all')

// Site config
export const getSiteConfig = (keys) => api.get('/site-config', { params: { keys } })

// Feedback
export const submitFeedback = (data) => api.post('/feedback', data)

// Verify
export const submitVerify = (data) => api.post('/verify/submit', data)
export const getVerifyStatus = () => api.get('/verify/status')

// Admin
export const adminDashboard = () => api.get('/admin/dashboard')
export const adminListUsers = (params) => api.get('/admin/users', { params })
export const adminCreateUser = (data) => api.post('/admin/users', data)
export const adminUpdateUser = (id, data) => api.put(`/admin/users/${id}`, data)
export const adminDeleteUser = (id) => api.delete(`/admin/users/${id}`)
export const adminToggleStatus = (id, data) => api.put(`/admin/users/${id}/status`, data)
export const adminRemoveVip = (id) => api.post(`/admin/users/${id}/remove-vip`)
export const adminWarnUser = (id, data) => api.post(`/admin/users/${id}/warn`, data)
export const adminReviewQueue = (params) => api.get('/admin/review-queue', { params })
export const adminApprove = (id) => api.post(`/admin/review-queue/${id}/approve`)
export const adminReject = (id, data) => api.post(`/admin/review-queue/${id}/reject`, data)
export const adminBatchReview = (data) => api.post('/admin/review-queue/batch', data)
export const adminBatchDelete = (data) => api.post('/admin/review-queue/batch-delete', data)
export const adminGenerateCards = (data) => api.post('/admin/cards/generate', data)
export const adminListBatches = () => api.get('/admin/cards/batches')
export const adminBatchDetail = (id, params) => api.get(`/admin/cards/batches/${id}`, { params })
export const adminDeleteCard = (id) => api.delete(`/admin/cards/${id}`)
export const adminExportBatch = (id) => api.get(`/admin/cards/batches/${id}/export`)
export const adminChats = () => api.get('/admin/chats')
export const adminChatMsgs = (id) => api.get(`/admin/chats/${id}/messages`)
export const adminReports = (params) => api.get('/admin/reports', { params })
export const adminHandleReport = (id, data) => api.post(`/admin/reports/${id}/handle`, data)
export const adminSensitiveWords = () => api.get('/admin/sensitive-words')
export const adminSiteConfigs = () => api.get('/admin/site-configs')
export const adminUpdateConfig = (key, data) => api.put(`/admin/site-configs/${key}`, data)

// 图片 URL 辅助函数（staging 图片通过 token 鉴权访问）
export const userImageUrl = (p) => {
  if (!p) return ''
  // 公开图片直接返回
  if (p.startsWith('/public/')) return p
  // staging 或其他受保护图片通过 /api/image 访问
  const t = localStorage.getItem('user_token') || ''
  return `/api/image?path=${encodeURIComponent(p)}&token=${t}`
}
