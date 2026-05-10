<template>
  <div class="up-page">
    <van-nav-bar title="用户资料" left-arrow fixed placeholder @click-left="$router.back()" />
    <div class="up-header">
      <van-image round width="70" height="70" :src="profile?.avatarUrl || ''" />
      <h3>{{ profile?.nickname || profile?.username }}</h3>
      <van-tag v-if="mutual" type="success">互相关注</van-tag>
      <p>{{ profile?.bio }}</p>
      <div class="up-actions">
        <van-button v-if="!followStatus.iFollow" type="primary" size="small" @click="toggleFollow">关注</van-button>
        <van-button v-else type="default" size="small" @click="toggleFollow">取消关注</van-button>
        <van-button type="primary" size="small" @click="startChat">发消息</van-button>
        <van-button type="danger" size="small" @click="blockUser">拉黑</van-button>
      </div>
    </div>
    <van-cell-group inset>
      <van-cell title="动态" :value="momentCount?.toString()" />
      <van-cell title="粉丝" :value="followerCount?.toString()" />
      <van-cell title="关注" :value="followingCount?.toString()" />
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { showSuccessToast, showFailToast } from 'vant';
import client from '../api/client';

const route = useRoute();
const router = useRouter();
const profile = ref<any>(null);
const followStatus = ref({ iFollow: false, theyFollow: false, mutual: false });
const mutual = ref(false);
const momentCount = ref(0);
const followerCount = ref(0);
const followingCount = ref(0);

const userId = route.params.id as string;

onMounted(async () => {
  try {
    const [pf, fs] = await Promise.all([
      client.get(`/users/${userId}`),
      client.get(`/follow/status/${userId}`),
    ]);
    profile.value = pf.data;
    followStatus.value = fs.data;
    mutual.value = fs.data.mutual;
    momentCount.value = pf.data.momentCount;
    followerCount.value = pf.data.followerCount;
    followingCount.value = pf.data.followingCount;
  } catch {}
});

async function toggleFollow() {
  try {
    if (followStatus.value.iFollow) {
      await client.delete(`/follow/${userId}`);
      followStatus.value.iFollow = false;
      mutual.value = false;
    } else {
      const res = await client.post(`/follow/${userId}`);
      followStatus.value.iFollow = true;
      mutual.value = res.data.mutual;
    }
  } catch {}
}

async function startChat() {
  try {
    const res = await client.post('/conversations', { targetUserId: userId });
    router.push(`/chat/${res.data.id}`);
  } catch (e: any) {
    showFailToast(e.response?.data?.error || '操作失败');
  }
}

async function blockUser() {
  try {
    await client.post(`/blacklist/${userId}`);
    showSuccessToast('已拉黑');
    router.back();
  } catch {}
}
</script>

<style scoped>
.up-page { background: #f7f8fa; min-height: 100vh; }
.up-header { text-align: center; padding: 20px; background: #fff; margin-bottom: 16px; }
.up-header h3 { margin: 8px 0; }
.up-actions { display: flex; gap: 8px; justify-content: center; margin-top: 12px; }
</style>
