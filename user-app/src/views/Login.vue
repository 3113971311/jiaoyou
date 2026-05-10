<template>
  <div class="login-page">
    <div class="login-card glass-card">
      <h2>拾光</h2>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="doLogin">
            <el-input v-model="l.account" placeholder="用户名/邮箱" style="margin-bottom:12px" />
            <el-input v-model="l.password" type="password" placeholder="密码" show-password style="margin-bottom:16px" />
            <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button>
            <el-button link type="primary" @click="tab='reset'" style="margin-top:8px">忘记密码?</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form @submit.prevent="doRegister">
            <el-input v-model="r.username" placeholder="用户名" style="margin-bottom:10px" />
            <el-input v-model="r.email" placeholder="邮箱" style="margin-bottom:10px" />
            <el-input v-model="r.password" type="password" placeholder="密码(至少6位)" show-password style="margin-bottom:10px" />
            <div style="display:flex;gap:8px;margin-bottom:16px">
              <el-input v-model="r.code" placeholder="验证码" /><el-button :disabled="cd>0" @click="sendVerifCode">{{ cd>0 ? cd+'s' : '获取验证码' }}</el-button>
            </div>
            <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">注册</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="找回密码" name="reset">
          <el-form @submit.prevent="doReset">
            <el-input v-model="f.email" placeholder="邮箱" style="margin-bottom:10px" />
            <div style="display:flex;gap:8px;margin-bottom:10px">
              <el-input v-model="f.code" placeholder="验证码" /><el-button :disabled="cd>0" @click="sendResetCode">{{ cd>0 ? cd+'s' : '获取验证码' }}</el-button>
            </div>
            <el-input v-model="f.pwd" type="password" placeholder="新密码" show-password style="margin-bottom:16px" />
            <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">重置密码</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { login, register, sendCode, resetPwd } from '../api'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const auth = useAuthStore()
const tab = ref('login')
const loading = ref(false)
const cd = ref(0)
const l = reactive({ account: '', password: '' })
const r = reactive({ username: '', email: '', password: '', code: '' })
const f = reactive({ email: '', code: '', pwd: '' })

let timer = null
function startCd() { cd.value=60; clearInterval(timer); timer=setInterval(()=>{ cd.value--; if(cd.value<=0)clearInterval(timer) },1000) }

async function sendVerifCode() {
  if (!r.email) return ElMessage.warning('请输入邮箱')
  try { await sendCode({ email: r.email, purpose: 'register' }); ElMessage.success('已发送'); startCd() } catch(e) { ElMessage.error(e.response?.data?.detail || '发送失败') }
}
async function sendResetCode() {
  if (!f.email) return ElMessage.warning('请输入邮箱')
  try { await sendCode({ email: f.email, purpose: 'reset_password' }); ElMessage.success('已发送'); startCd() } catch(e) { ElMessage.error(e.response?.data?.detail || '发送失败') }
}

async function doLogin() {
  loading.value = true
  try {
    const res = await login({ account: l.account, password: l.password })
    localStorage.setItem('user_token', res.data.access_token || res.data.accessToken)
    await auth.fetchMe()
    ElMessage.success('登录成功')
    router.push('/')
  } catch(e) { ElMessage.error(e.response?.data?.detail || '登录失败') }
  finally { loading.value = false }
}

async function doRegister() {
  loading.value = true
  try {
    const res = await register(r)
    localStorage.setItem('user_token', res.data.access_token || res.data.accessToken)
    await auth.fetchMe()
    ElMessage.success('注册成功')
    router.push('/')
  } catch(e) { ElMessage.error(e.response?.data?.detail || '注册失败') }
  finally { loading.value = false }
}

async function doReset() {
  loading.value = true
  try {
    await resetPwd({ email: f.email, code: f.code, new_password: f.pwd })
    ElMessage.success('密码已重置')
    tab.value = 'login'
  } catch(e) { ElMessage.error(e.response?.data?.detail || '重置失败') }
  finally { loading.value = false }
}
</script>
