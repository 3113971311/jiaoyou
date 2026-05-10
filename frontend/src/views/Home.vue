<template>
  <div class="page-container">
    <div v-if="!auth.isVip" class="glass-card" style="margin-bottom:16px;text-align:center;cursor:pointer" @click="$router.push('/vip')">
      <span style="color:var(--accent);font-weight:600">开通VIP会员，解锁全部功能 →</span>
    </div>

    <el-row :gutter="16">
      <el-col :span="6" v-for="item in shortcuts" :key="item.label">
        <div class="glass-card stat-card" @click="$router.push(item.path)" style="cursor:pointer">
          <el-icon :size="28" :color="item.color"><component :is="item.icon" /></el-icon>
          <div style="font-size:14px;font-weight:600;margin-top:8px">{{ item.label }}</div>
        </div>
      </el-col>
    </el-row>

    <h3 style="margin:24px 0 12px">最新动态</h3>
    <el-empty v-if="!moments.length" description="暂无动态" />
    <div v-for="m in moments" :key="m.id" class="glass-card" style="margin-bottom:12px">
      <div style="font-weight:600">{{ m.user?.nickname || m.user?.username }}</div>
      <div v-if="m.content_text">{{ m.content_text.slice(0, 120) }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getFeed } from '../api'
import { Search, ChatDotRound, Star, Money } from '@element-plus/icons-vue'

const auth = useAuthStore()
const moments = ref([])
const shortcuts = [
  { label: '匹配', icon: Search, path: '/match', color: '#007aff' },
  { label: '聊天', icon: ChatDotRound, path: '/chat', color: '#34c759' },
  { label: '动态', icon: Star, path: '/moments', color: '#ff9500' },
  { label: 'VIP', icon: Money, path: '/vip', color: '#ff3b30' },
]

onMounted(async () => {
  try { const r = await getFeed(); moments.value = r.data.list || [] } catch {}
})
</script>
