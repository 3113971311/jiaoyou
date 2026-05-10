<template>
  <div class="page-container" style="max-width:500px;margin:0 auto">
    <div class="glass-card" style="text-align:center">
      <el-image :src="auth.user?.avatar_url||''" style="width:80px;height:80px;border-radius:50%" @click="changeAvatar" />
      <h3 style="margin-top:12px">{{ auth.user?.nickname||auth.user?.username }}</h3>
      <p v-if="auth.isVip" style="color:#ff9500;font-weight:600">VIP会员</p>
      <p v-if="auth.user?.location" style="color:var(--text-secondary);font-size:13px"><el-icon><Location /></el-icon> {{ auth.user.location }}</p>
      <p style="color:var(--text-secondary);font-size:13px">{{ auth.user?.bio||'暂无简介' }}</p>
    </div>
    <div class="glass-card" style="margin-top:12px">
      <div class="menu-item" @click="$router.push('/following')">关注 <span style="color:var(--text-secondary)">→</span></div>
      <div class="menu-item" @click="$router.push('/followers')">粉丝 <span style="color:var(--text-secondary)">→</span></div>
      <div class="menu-item" @click="$router.push('/vip')">VIP <span style="color:var(--text-secondary)">{{ auth.isVip?'已开通':'未开通' }} →</span></div>
    </div>
    <div class="glass-card" style="margin-top:12px">
      <div class="menu-item" @click="$router.push('/notifications')">通知 →</div>
      <div class="menu-item" @click="$router.push('/settings')">编辑资料 →</div>
      <div class="menu-item" @click="$router.push('/feedback')">问题反馈 →</div>
    </div>
    <el-button style="width:100%;margin-top:20px" @click="auth.logout()">退出登录</el-button>
    <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="onAvatarChange" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { uploadAvatar } from '../api'
const auth = useAuthStore()
const avatarInput = ref(null)
function changeAvatar() { avatarInput.value?.click() }
async function onAvatarChange(e) { const f=e.target.files[0]; if(!f) return; const fd=new FormData(); fd.append('file',f); try { await uploadAvatar(fd); ElMessage.success('头像已上传，等待审核') } catch {} }
</script>
