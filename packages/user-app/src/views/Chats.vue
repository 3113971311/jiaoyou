<template>
  <div class="chats-page">
    <van-nav-bar title="消息" fixed placeholder />
    <van-cell-group inset v-if="conversations.length">
      <van-cell v-for="c in conversations" :key="c.id" @click="$router.push(`/chat/${c.id}`)" :title="c.otherUser?.nickname || c.otherUser?.username" :label="c.lastMessage?.content || ''" is-link>
        <template #icon><van-image round width="40" height="40" :src="c.otherUser?.avatarUrl || ''" /></template>
      </van-cell>
    </van-cell-group>
    <van-empty v-else description="暂无消息" />
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
import client from '../api/client';

const active = ref(2);
const conversations = ref<any[]>([]);

onMounted(async () => {
  try {
    const res = await client.get('/conversations');
    conversations.value = res.data.list || [];
  } catch {}
});
</script>

<style scoped>
.chats-page { background: #f7f8fa; min-height: 100vh; padding-bottom: 60px; }
</style>
