<template>
  <div class="profile-page">
    <div class="profile-header">
      <van-image round width="70" height="70" :src="user?.avatarUrl || ''" @click="onChangeAvatar" />
      <h3>{{ user?.nickname || user?.username }}</h3>
      <p v-if="auth.isVip" class="vip-tag">VIP</p>
      <p>{{ user?.bio || '这个人很懒，什么都没写' }}</p>
      <p class="location" v-if="user?.location"><van-icon name="location-o" /> {{ user.location }}</p>
    </div>

    <van-cell-group inset>
      <van-cell title="关注" :value="user?.followingCount" is-link to="/following" />
      <van-cell title="粉丝" :value="user?.followerCount" is-link to="/followers" />
      <van-cell title="VIP" :value="auth.isVip ? '已开通' : '未开通'" is-link to="/vip" />
    </van-cell-group>

    <van-cell-group inset style="margin-top:16px">
      <van-cell title="通知" icon="bell" is-link to="/notifications" />
      <van-cell title="编辑资料" icon="setting-o" is-link to="/settings" />
      <van-cell title="问题反馈" icon="comment-o" is-link to="/feedback" />
      <van-cell title="关于我们" is-link />
    </van-cell-group>

    <div class="logout-btn"><van-button block type="default" @click="auth.logout()">退出登录</van-button></div>

    <van-tabbar v-model="active">
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="search" to="/match">匹配</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/chat">聊天</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import client from '../api/client';
import { showSuccessToast } from 'vant';

const auth = useAuthStore();
const active = ref(3);
const user = computed(() => auth.user);

onMounted(async () => {
  // 自动刷新用户信息以获取最新关注数
  try { await auth.fetchMe(); } catch {}
});

async function onChangeAvatar() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      await client.post('/users/avatar', form);
      showSuccessToast('头像已上传，等待审核');
    } catch {}
  };
  input.click();
}
</script>

<style scoped>
.profile-page { background: #f7f8fa; min-height: 100vh; padding-bottom: 60px; }
.profile-header { text-align: center; padding: 30px 20px; background: #fff; }
.profile-header h3 { margin: 10px 0 4px; }
.vip-tag { display: inline-block; background: linear-gradient(135deg, #ff6b6b, #ff8e53); color: #fff; padding: 2px 10px; border-radius: 10px; font-size: 12px; }
.location { color: #999; font-size: 13px; margin-top: 4px; display: flex; align-items: center; justify-content: center; gap: 4px; }
.logout-btn { padding: 30px 16px; }
</style>
