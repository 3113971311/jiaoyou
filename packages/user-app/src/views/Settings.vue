<template>
  <div class="settings-page">
    <van-nav-bar title="设置" left-arrow fixed placeholder @click-left="$router.back()" />
    <van-cell-group inset title="个人资料">
      <van-field v-model="form.nickname" label="昵称" placeholder="输入昵称" />
      <van-field name="gender" label="性别">
        <template #input><van-radio-group v-model="form.gender" direction="horizontal"><van-radio name="male">男</van-radio><van-radio name="female">女</van-radio></van-radio-group></template>
      </van-field>
      <van-field v-model="form.bio" label="简介" type="textarea" rows="3" maxlength="200" />
      <div class="save-btn"><van-button block type="primary" @click="saveProfile">保存资料</van-button></div>
    </van-cell-group>

    <van-cell-group inset style="margin-top:16px">
      <van-field v-model="pw.oldPassword" label="原密码" type="password" />
      <van-field v-model="pw.newPassword" label="新密码" type="password" />
      <div class="save-btn"><van-button block type="primary" @click="changePw">修改密码</van-button></div>
    </van-cell-group>

    <div class="blacklist-link"><van-cell title="黑名单管理" is-link to="/blacklist" /></div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import { showSuccessToast, showFailToast } from 'vant';
import { useAuthStore } from '../stores/auth';
import client from '../api/client';

const auth = useAuthStore();
const form = reactive({ nickname: '', gender: '', bio: '' });
const pw = reactive({ oldPassword: '', newPassword: '' });

onMounted(() => {
  const u = auth.user;
  if (u) Object.assign(form, { nickname: u.nickname || '', gender: u.gender || '', bio: u.bio || '' });
});

async function saveProfile() {
  try {
    await client.put('/users/profile', form);
    showSuccessToast('已保存');
    auth.fetchMe();
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '保存失败');
  }
}

async function changePw() {
  try {
    await client.put('/auth/password', pw);
    showSuccessToast('密码已修改');
    pw.oldPassword = '';
    pw.newPassword = '';
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '修改失败');
  }
}
</script>
<style scoped>
.settings-page { background: #f7f8fa; min-height: 100vh; }
.save-btn { padding: 12px 16px; }
.blacklist-link { margin-top: 20px; }
</style>
