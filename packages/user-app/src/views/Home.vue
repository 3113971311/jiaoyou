<template>
  <div class="home">
    <!-- 顶部 -->
    <div class="header">
      <h2>交友聊天</h2>
      <van-icon name="bell" size="22" :badge="unreadCount || ''" @click="$router.push('/notifications')" />
    </div>

    <!-- 通知跑马灯 -->
    <div class="notif-banner" v-if="latestNotif" @click="$router.push('/notifications')">
      <van-icon name="volume-o" /> {{ latestNotif.title }}：{{ latestNotif.content }}
    </div>

    <!-- 公告 -->
    <div class="announce" v-if="announce" v-html="announce"></div>

    <!-- VIP 状态 -->
    <div class="vip-bar" v-if="!auth.isVip" @click="$router.push('/vip')">
      开通VIP会员，解锁全部功能 →
    </div>

    <!-- 快捷入口 -->
    <van-grid :column-num="4" class="quick">
      <van-grid-item icon="friends-o" text="匹配" to="/match" />
      <van-grid-item icon="chat-o" text="聊天" to="/chat" />
      <van-grid-item icon="photo-o" text="动态" to="/moments" />
      <van-grid-item icon="user-o" text="我的" to="/profile" />
    </van-grid>

    <!-- 最新动态预览 -->
    <div class="section-title">最新动态</div>
    <div class="feed-preview" v-if="previewMoments.length">
      <div class="moment-card" v-for="m in previewMoments" :key="m.id" @click="$router.push('/moments')">
        <div class="mc-header">
          <span class="mc-name">{{ m.user?.nickname || m.user?.username }}</span>
        </div>
        <div class="mc-text" v-if="m.contentText">{{ m.contentText.slice(0, 100) }}</div>
        <div class="mc-images" v-if="m.images?.length">
          <img v-for="(img, i) in m.images.slice(0, 3)" :key="i" :src="img.thumb || img.url" />
        </div>
      </div>
    </div>
    <van-empty v-else description="暂无动态，去关注一些人吧" />

    <!-- 底部导航 -->
    <van-tabbar v-model="active">
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="search" to="/match">匹配</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/chat">聊天</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import client from '../api/client';

const auth = useAuthStore();
const active = ref(0);
const unreadCount = ref(0);
const announce = ref('');
const previewMoments = ref<any[]>([]);
const latestNotif = ref<any>(null);

onMounted(async () => {
  // 拉取公告
  try {
    const res = await client.get('/site-config?keys=announcement');
    announce.value = res.data.announcement?.value || '';
  } catch {}
  // 拉取最新通知
  try {
    const res = await client.get('/notifications', { params: { limit: 1 } });
    if (res.data.items?.length) {
      const notif = res.data.items[0];
      if (!notif.isRead) latestNotif.value = notif;
    }
    unreadCount.value = res.data.unreadCount || 0;
  } catch {}
  // 拉取动态预览
  try {
    const res = await client.get('/moments', { params: { limit: 3 } });
    previewMoments.value = res.data.list || [];
  } catch {}
});
</script>

<style scoped>
.home { min-height: 100vh; background: #f7f8fa; padding-bottom: 60px; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #fff; }
.header h2 { margin: 0; font-size: 20px; }
.notif-banner { margin: 8px 12px; padding: 10px 12px; background: #fff0f0; border-radius: 8px; font-size: 13px; color: #e63946; display: flex; align-items: center; gap: 6px; animation: slideIn 0.3s; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; cursor: pointer; }
@keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.announce { margin: 8px 12px; padding: 10px; background: #fff7e6; border-radius: 8px; font-size: 13px; color: #e6a23c; }
.vip-bar { margin: 8px 12px; padding: 12px; background: linear-gradient(135deg, #ff6b6b, #ff8e53); color: #fff; text-align: center; border-radius: 8px; font-size: 14px; }
.quick { background: #fff; margin-bottom: 10px; }
.section-title { padding: 12px 16px 4px; font-size: 15px; font-weight: bold; }
.feed-preview { padding: 0 12px; }
.moment-card { background: #fff; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.mc-header { margin-bottom: 6px; }
.mc-name { font-weight: bold; font-size: 14px; }
.mc-text { font-size: 14px; color: #333; line-height: 1.5; margin-bottom: 6px; }
.mc-images { display: flex; gap: 4px; }
.mc-images img { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; }
</style>
