<template>
  <div class="login-page">
    <div class="glass-card login-card">
      <h2 class="login-card-title">管理后台登录</h2>
      <el-input v-model="account" placeholder="管理员账号" size="large" style="margin-bottom:12px" />
      <el-input v-model="password" type="password" placeholder="密码" show-password size="large" style="margin-bottom:20px" @keyup.enter="doLogin" />
      <el-button type="primary" size="large" :loading="loading" style="width:100%" @click="doLogin">登 录</el-button>
      <div v-if="errMsg" style="color:var(--danger);text-align:center;margin-top:12px;font-size:13px">{{ errMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const account = ref('admin')
const password = ref('admin123456')
const loading = ref(false)
const errMsg = ref('')

async function doLogin() {
  errMsg.value = ''
  if (!account.value || !password.value) { errMsg.value = '请输入账号和密码'; return }
  loading.value = true
  try {
    const res = await axios.post('/api/auth/login', { account: account.value, password: password.value })
    if (!res.data.access_token) { errMsg.value = '响应异常：' + JSON.stringify(res.data); return }
    localStorage.setItem('admin_token', res.data.access_token)
    const me = await axios.get('/api/auth/me', { headers: { Authorization: 'Bearer ' + res.data.access_token } })
    if (!me.data.is_admin) { errMsg.value = '非管理员账号'; localStorage.clear(); return }
    router.push('/')
  } catch(e) {
    errMsg.value = e.response?.data?.detail || e.message || '登录失败'
  } finally { loading.value = false }
}
</script>
