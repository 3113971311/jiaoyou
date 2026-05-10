<template>
  <div class="page">
    <van-nav-bar title="我的粉丝" left-arrow fixed placeholder @click-left="$router.back()" />
    <van-cell-group inset v-if="list.length">
      <van-cell v-for="u in list" :key="u.id" :title="u.nickname || u.username" :label="u.gender === 'male' ? '男' : u.gender === 'female' ? '女' : ''" is-link @click="$router.push('/profile/' + u.id)">
        <template #icon><van-image round width="40" height="40" :src="u.avatarUrl || ''" /></template>
      </van-cell>
    </van-cell-group>
    <van-empty v-else description="暂无粉丝" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import client from '../api/client';
const list = ref<any[]>([]);
onMounted(async () => {
  const res = await client.get('/follow/followers');
  list.value = res.data.list || [];
});
</script>
