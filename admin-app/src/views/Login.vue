<template>
  <div class="login-page">
    <div class="glass-card login-card">
      <h2 class="login-card-title">管理后台登录</h2>
      <el-input
        v-model="account"
        placeholder="管理员账号"
        size="large"
        style="margin-bottom: 12px"
      />
      <el-input
        v-model="password"
        type="password"
        placeholder="密码"
        show-password
        size="large"
        style="margin-bottom: 20px"
        @keyup.enter="doLogin"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        style="width: 100%"
        @click="doLogin"
      >
        登录
      </el-button>
      <div
        v-if="errMsg"
        style="color: var(--danger); text-align: center; margin-top: 12px; font-size: 13px"
      >
        {{ errMsg }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { clearAdminAuth, setAdminAuthTokens } from '../api'

const router = useRouter()
const account = ref('')
const password = ref('')
const loading = ref(false)
const errMsg = ref('')

async function doLogin() {
  errMsg.value = ''
  if (!account.value || !password.value) {
    errMsg.value = '请输入账号和密码'
    return
  }

  loading.value = true
  try {
    const res = await axios.post('/api/auth/login', {
      account: account.value,
      password: password.value,
    })

    if (!res.data.access_token) {
      errMsg.value = `响应异常: ${JSON.stringify(res.data)}`
      return
    }

    setAdminAuthTokens(res.data.access_token, res.data.refresh_token || '')

    const me = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${res.data.access_token}` },
    })

    if (!me.data.is_admin) {
      errMsg.value = '当前账号不是管理员'
      clearAdminAuth()
      return
    }

    router.push('/')
  } catch (error) {
    errMsg.value = error.response?.data?.detail || error.message || '登录失败'
    clearAdminAuth()
  } finally {
    loading.value = false
  }
}
</script>
