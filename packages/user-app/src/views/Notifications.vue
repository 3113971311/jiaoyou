<template>
  <div class="notif-page">
    <van-nav-bar title="通知" fixed placeholder left-arrow @click-left="$router.back()">
      <template #right><span @click="readAll" style="color:#1989fa">全部已读</span></template>
    </van-nav-bar>
    <van-cell-group inset>
      <van-cell v-for="n in items" :key="n.id" :title="n.title" :label="n.content" @click="readOne(n)">
        <template #icon><van-badge :dot="!n.isRead"><van-icon name="envelope-o" size="20" /></van-badge></template>
      </van-cell>
    </van-cell-group>
    <van-empty v-if="!items.length" description="暂无通知" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import client from '../api/client';

const items = ref<any[]>([]);

onMounted(async () => {
  try {
    const res = await client.get('/notifications');
    items.value = res.data.items || [];
  } catch {}
});

async function readOne(n: any) {
  if (!n.isRead) {
    await client.put(`/notifications/${n.id}/read`);
    n.isRead = true;
  }
}

async function readAll() {
  await client.put('/notifications/read-all');
  items.value.forEach((n) => (n.isRead = true));
}
</script>
<style scoped>.notif-page { background: #f7f8fa; min-height: 100vh; }</style>
