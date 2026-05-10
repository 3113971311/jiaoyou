<template>
  <div class="admin-login">
    <el-card class="login-card">
      <h2>管理后台</h2>
      <el-form @submit.prevent="onLogin">
        <el-form-item><el-input v-model="account" placeholder="用户名/邮箱" /></el-form-item>
        <el-form-item><el-input v-model="password" type="password" placeholder="密码" show-password /></el-form-item>
        <el-form-item><el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button></el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import client from '../api/client';
import router from '../router';

const account = ref('');
const password = ref('');
const loading = ref(false);

async function onLogin() {
  loading.value = true;
  try {
    const res = await client.post('/auth/login', { account: account.value, password: password.value });
    localStorage.setItem('adminToken', res.data.accessToken);
    // 验证是管理员
    const me = await client.get('/auth/me');
    if (!me.data.isAdmin) {
      ElMessage.error('非管理员账号');
      localStorage.clear();
      return;
    }
    router.push('/');
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || '登录失败');
  } finally { loading.value = false; }
}
</script>

<style scoped>
.admin-login { height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f2f5; }
.login-card { width: 380px; }
.login-card h2 { text-align: center; margin-bottom: 24px; }
</style>
