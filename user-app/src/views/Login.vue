<template>
  <div class="login-page">
    <div class="login-card glass-card">
      <h2>拾光</h2>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="doLogin">
            <el-input
              v-model="loginForm.account"
              placeholder="用户名或邮箱"
              style="margin-bottom: 12px"
            />
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              show-password
              style="margin-bottom: 16px"
            />
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              style="width: 100%"
            >
              登录
            </el-button>
            <el-button link type="primary" @click="tab = 'reset'" style="margin-top: 8px">
              忘记密码？
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form @submit.prevent="doRegister">
            <el-input
              v-model="registerForm.username"
              placeholder="用户名"
              style="margin-bottom: 10px"
            />
            <el-input
              v-model="registerForm.email"
              placeholder="邮箱"
              style="margin-bottom: 10px"
            />
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="密码（至少 6 位）"
              show-password
              style="margin-bottom: 10px"
            />
            <div style="display: flex; gap: 8px; margin-bottom: 16px">
              <el-input v-model="registerForm.code" placeholder="验证码" />
              <el-button :disabled="countdown > 0" @click="sendRegisterCode">
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </el-button>
            </div>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              style="width: 100%"
            >
              注册
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="找回密码" name="reset">
          <el-form @submit.prevent="doReset">
            <el-input v-model="resetForm.email" placeholder="邮箱" style="margin-bottom: 10px" />
            <div style="display: flex; gap: 8px; margin-bottom: 10px">
              <el-input v-model="resetForm.code" placeholder="验证码" />
              <el-button :disabled="countdown > 0" @click="sendResetCode">
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </el-button>
            </div>
            <el-input
              v-model="resetForm.password"
              type="password"
              placeholder="新密码"
              show-password
              style="margin-bottom: 16px"
            />
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              style="width: 100%"
            >
              重置密码
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { login, register, resetPwd, sendCode, setUserAuthTokens } from '../api'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const auth = useAuthStore()
const tab = ref('login')
const loading = ref(false)
const countdown = ref(0)

const loginForm = reactive({ account: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', code: '' })
const resetForm = reactive({ email: '', code: '', password: '' })

let timer = null

function startCountdown() {
  countdown.value = 60
  clearInterval(timer)
  timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

function saveTokens(data) {
  setUserAuthTokens(data.access_token || data.accessToken || '', data.refresh_token || '')
}

async function sendRegisterCode() {
  if (!registerForm.email) {
    ElMessage.warning('请输入邮箱')
    return
  }
  try {
    await sendCode({ email: registerForm.email, purpose: 'register' })
    ElMessage.success('验证码已发送')
    startCountdown()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
  }
}

async function sendResetCode() {
  if (!resetForm.email) {
    ElMessage.warning('请输入邮箱')
    return
  }
  try {
    await sendCode({ email: resetForm.email, purpose: 'reset_password' })
    ElMessage.success('验证码已发送')
    startCountdown()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
  }
}

async function doLogin() {
  loading.value = true
  try {
    const res = await login({
      account: loginForm.account,
      password: loginForm.password,
    })
    saveTokens(res.data)
    await auth.fetchMe()
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  loading.value = true
  try {
    const res = await register(registerForm)
    saveTokens(res.data)
    await auth.fetchMe()
    ElMessage.success('注册成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}

async function doReset() {
  loading.value = true
  try {
    await resetPwd({
      email: resetForm.email,
      code: resetForm.code,
      new_password: resetForm.password,
    })
    ElMessage.success('密码已重置')
    tab.value = 'login'
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '重置失败')
  } finally {
    loading.value = false
  }
}
</script>
