<template>
  <div class="login-page">
    <div class="logo-area">
      <h1>交友聊天</h1>
      <p>遇见有趣的人</p>
    </div>

    <van-tabs v-model:active="activeTab" type="card">
      <van-tab title="登录">
        <van-form @submit="onLogin" class="form">
          <van-cell-group inset>
            <van-field v-model="loginForm.account" label="账号" placeholder="用户名/邮箱" :rules="[{ required: true }]" />
            <van-field v-model="loginForm.password" label="密码" type="password" placeholder="输入密码" :rules="[{ required: true }]" />
          </van-cell-group>
          <div class="btn-area"><van-button block type="primary" native-type="submit" :loading="loading">登录</van-button></div>
          <div class="link"><span @click="activeTab = 'reset'">忘记密码?</span></div>
        </van-form>
      </van-tab>

      <van-tab title="注册">
        <van-form @submit="onRegister" class="form">
          <van-cell-group inset>
            <van-field v-model="regForm.username" label="用户名" placeholder="3-20位" :rules="[{ required: true, pattern: /^[\w\u4e00-\u9fa5]{3,20}$/, message: '3-20位字母/数字/中文/下划线' }]" />
            <van-field v-model="regForm.email" label="邮箱" placeholder="输入QQ邮箱" :rules="[{ required: true, pattern: /^\S+@\S+$/, message: '邮箱格式不对' }]" />
            <van-field v-model="regForm.password" label="密码" type="password" placeholder="至少6位" :rules="[{ required: true, min: 6 }]" />
            <van-field v-model="regForm.code" label="验证码" placeholder="6位数字" center :rules="[{ required: true }]">
              <template #button>
                <van-button size="small" type="primary" @click="sendCode('register')" :disabled="codeCd > 0">{{ codeCd > 0 ? `${codeCd}s` : '获取验证码' }}</van-button>
              </template>
            </van-field>
          </van-cell-group>
          <div class="btn-area"><van-button block type="primary" native-type="submit" :loading="loading">注册</van-button></div>
        </van-form>
      </van-tab>

      <van-tab title="找回密码">
        <van-form @submit="onReset" class="form">
          <van-cell-group inset>
            <van-field v-model="resetForm.email" label="邮箱" :rules="[{ required: true }]" />
            <van-field v-model="resetForm.code" label="验证码" center :rules="[{ required: true }]">
              <template #button>
                <van-button size="small" type="primary" @click="sendCode('reset_password')" :disabled="codeCd > 0">{{ codeCd > 0 ? `${codeCd}s` : '获取验证码' }}</van-button>
              </template>
            </van-field>
            <van-field v-model="resetForm.newPassword" label="新密码" type="password" :rules="[{ required: true, min: 6 }]" />
          </van-cell-group>
          <div class="btn-area"><van-button block type="primary" native-type="submit" :loading="loading">重置密码</van-button></div>
        </van-form>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { showSuccessToast, showFailToast } from 'vant';
import client from '../api/client';
import { useAuthStore } from '../stores/auth';
import router from '../router';

const auth = useAuthStore();
const activeTab = ref('login');
const loading = ref(false);
const codeCd = ref(0);

const loginForm = reactive({ account: '', password: '' });
const regForm = reactive({ username: '', email: '', password: '', code: '' });
const resetForm = reactive({ email: '', code: '', newPassword: '' });

let cdTimer: any = null;

function startCountdown() {
  if (cdTimer) clearInterval(cdTimer);
  codeCd.value = 60;
  cdTimer = setInterval(() => {
    codeCd.value--;
    if (codeCd.value <= 0) { clearInterval(cdTimer); cdTimer = null; }
  }, 1000);
}

async function sendCode(purpose: string) {
  const email = purpose === 'register' ? regForm.email : resetForm.email;
  if (!email) { showFailToast('请先输入邮箱'); return; }
  // 无论成功失败都启动倒计时，与服务器限流保持同步
  startCountdown();
  try {
    await client.post('/auth/send-verify-code', { email, purpose });
    showSuccessToast('验证码已发送');
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '发送失败');
  }
}

async function onLogin() {
  loading.value = true;
  try {
    await auth.login(loginForm.account, loginForm.password);
    showSuccessToast('登录成功');
    router.push('/');
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '登录失败');
  } finally { loading.value = false; }
}

async function onRegister() {
  loading.value = true;
  try {
    const res = await client.post('/auth/register', regForm);
    localStorage.setItem('accessToken', res.data.accessToken);
    localStorage.setItem('refreshToken', res.data.refreshToken);
    await auth.fetchMe();
    showSuccessToast('注册成功');
    router.push('/');
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '注册失败');
  } finally { loading.value = false; }
}

async function onReset() {
  loading.value = true;
  try {
    await client.post('/auth/reset-password', resetForm);
    showSuccessToast('密码已重置，请登录');
    activeTab.value = 'login';
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '重置失败');
  } finally { loading.value = false; }
}
</script>

<style scoped>
.login-page { min-height: 100vh; background: #f7f8fa; padding: 40px 0; }
.logo-area { text-align: center; margin-bottom: 30px; }
.logo-area h1 { font-size: 28px; color: #1989fa; margin: 0; }
.logo-area p { color: #999; margin-top: 6px; }
.form { padding: 16px; }
.btn-area { padding: 20px 16px; }
.link { text-align: center; color: #1989fa; font-size: 14px; }
</style>
